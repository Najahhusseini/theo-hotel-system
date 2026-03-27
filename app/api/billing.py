# app/api/billing.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.billing import Folio, Transaction, Invoice, TransactionType, PaymentMethod, InvoiceStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.guest import Guest
from app.models.room import Room
from app.models.user import User
from app.schemas.billing import (
    FolioCreate, FolioResponse, FolioSummary, FolioDetails,
    TransactionCreate, TransactionResponse,
    InvoiceCreate, InvoiceResponse, InvoiceUpdate,
    PaymentCreate, PaymentResponse, ChargeCreate
)
from app.utils.dependencies import (
    get_current_user, require_front_desk, require_accounting, require_hotel_manager
)

router = APIRouter(prefix="/billing", tags=["billing"])

def generate_folio_number():
    """Generate a unique folio number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"FOL-{timestamp}-{unique_id}"

def generate_transaction_number():
    """Generate a unique transaction number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"TXN-{timestamp}-{unique_id}"

def generate_invoice_number():
    """Generate a unique invoice number"""
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())[:6].upper()
    return f"INV-{timestamp}-{unique_id}"

def update_folio_totals(folio_id: int, db: Session):
    """Recalculate folio totals based on transactions"""
    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        return
    
    transactions = db.query(Transaction).filter(Transaction.folio_id == folio_id).all()
    
    subtotal = 0.0
    tax = 0.0
    paid = 0.0
    
    for t in transactions:
        if t.transaction_type.value == "payment":
            paid += abs(t.amount)
        else:
            subtotal += t.amount
            tax += t.tax
    
    total = subtotal + tax
    balance = total - paid
    
    folio.subtotal = subtotal
    folio.tax = tax
    folio.total = total
    folio.paid = paid
    folio.balance = balance
    
    db.commit()
    return folio

# ==================== CREATE FOLIO ====================
@router.post("/folios", response_model=FolioResponse, status_code=201)
def create_folio(
    folio_data: FolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Create a new folio for a reservation (Front Desk)
    """
    # Check if reservation exists
    reservation = db.query(Reservation).filter(Reservation.id == folio_data.reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Check if guest exists
    guest = db.query(Guest).filter(Guest.id == folio_data.guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Check if folio already exists for this reservation
    existing = db.query(Folio).filter(Folio.reservation_id == folio_data.reservation_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Folio already exists for this reservation")
    
    # Create folio
    new_folio = Folio(
        folio_number=generate_folio_number(),
        reservation_id=folio_data.reservation_id,
        guest_id=folio_data.guest_id,
        hotel_id=folio_data.hotel_id,
        is_open=True
    )
    
    db.add(new_folio)
    db.commit()
    db.refresh(new_folio)
    
    return new_folio

# ==================== GET FOLIO ====================
@router.get("/folios/{folio_id}", response_model=FolioResponse)
def get_folio(
    folio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Get folio details with all transactions
    """
    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    
    return folio

# ==================== GET FOLIO BY RESERVATION ====================
@router.get("/folios/reservation/{reservation_id}", response_model=FolioResponse)
def get_folio_by_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Get folio by reservation ID
    """
    folio = db.query(Folio).filter(Folio.reservation_id == reservation_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    
    return folio

# ==================== ADD CHARGE ====================
@router.post("/folios/{folio_id}/charges", response_model=TransactionResponse)
def add_charge(
    folio_id: int,
    charge: ChargeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Add a charge to a folio (Front Desk)
    """
    folio = db.query(Folio).filter(Folio.id == folio_id, Folio.is_open == True).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Open folio not found")
    
    # Create transaction
    transaction = Transaction(
        transaction_number=generate_transaction_number(),
        folio_id=folio_id,
        transaction_type=charge.transaction_type,
        description=charge.description,
        amount=charge.amount,
        tax=charge.tax,
        external_reference=charge.external_reference,
        processed_by_id=current_user.id
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Update folio totals
    update_folio_totals(folio_id, db)
    
    return transaction

# ==================== ADD PAYMENT ====================
@router.post("/folios/{folio_id}/payments", response_model=PaymentResponse)
def add_payment(
    folio_id: int,
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Add a payment to a folio (Front Desk)
    """
    folio = db.query(Folio).filter(Folio.id == folio_id, Folio.is_open == True).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Open folio not found")
    
    if payment.amount > folio.balance:
        raise HTTPException(
            status_code=400, 
            detail=f"Payment amount exceeds balance. Balance: ${folio.balance:.2f}"
        )
    
    # Create payment transaction (negative amount)
    transaction = Transaction(
        transaction_number=generate_transaction_number(),
        folio_id=folio_id,
        transaction_type=TransactionType.PAYMENT,
        description=payment.notes or f"Payment via {payment.payment_method.value}",
        amount=-payment.amount,  # Negative for payments
        tax=0,
        payment_method=payment.payment_method,
        payment_reference=payment.payment_reference,
        processed_by_id=current_user.id
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Update folio totals
    updated_folio = update_folio_totals(folio_id, db)
    
    return PaymentResponse(
        transaction_id=transaction.id,
        transaction_number=transaction.transaction_number,
        amount=payment.amount,
        payment_method=payment.payment_method,
        payment_reference=payment.payment_reference,
        new_balance=updated_folio.balance,
        message="Payment processed successfully"
    )

# ==================== CLOSE FOLIO (CHECKOUT) ====================
@router.post("/folios/{folio_id}/close")
def close_folio(
    folio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Close folio and mark as checked out (Front Desk)
    """
    folio = db.query(Folio).filter(Folio.id == folio_id, Folio.is_open == True).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Open folio not found")
    
    if folio.balance > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot close folio with outstanding balance: ${folio.balance:.2f}"
        )
    
    folio.is_open = False
    folio.is_checked_out = True
    folio.closed_at = datetime.now()
    
    # Update reservation status
    reservation = db.query(Reservation).filter(Reservation.id == folio.reservation_id).first()
    if reservation:
        reservation.status = "checked_out"
    
    db.commit()
    
    return {
        "message": "Folio closed successfully",
        "folio_number": folio.folio_number,
        "total_paid": folio.paid
    }

# ==================== CREATE INVOICE ====================
@router.post("/folios/{folio_id}/invoice", response_model=InvoiceResponse)
def create_invoice(
    folio_id: int,
    invoice_data: InvoiceCreate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_accounting)
):
    """
    Create an invoice from a folio (Accounting only)
    """
    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    
    # Check if invoice already exists
    existing = db.query(Invoice).filter(Invoice.folio_id == folio_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Invoice already exists for this folio")
    
    # Create invoice
    invoice = Invoice(
        invoice_number=generate_invoice_number(),
        folio_id=folio_id,
        reservation_id=folio.reservation_id,
        guest_id=folio.guest_id,
        amount=folio.subtotal,
        tax=folio.tax,
        total=folio.total,
        status=InvoiceStatus.DRAFT,
        due_date=invoice_data.due_date if invoice_data else None
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice

# ==================== GET INVOICE ====================
@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Get invoice by ID
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

# ==================== MARK INVOICE AS PAID ====================
@router.put("/invoices/{invoice_id}/pay")
def mark_invoice_paid(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_accounting)
):
    """
    Mark invoice as paid (Accounting only)
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = InvoiceStatus.PAID
    invoice.paid_date = datetime.now()
    db.commit()
    
    return {"message": "Invoice marked as paid", "invoice_number": invoice.invoice_number}

# ==================== GET FOLIO SUMMARY ====================
@router.get("/folios/{folio_id}/summary", response_model=FolioSummary)
def get_folio_summary(
    folio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Get a formatted summary of the folio
    """
    folio = db.query(Folio).filter(Folio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=404, detail="Folio not found")
    
    reservation = db.query(Reservation).filter(Reservation.id == folio.reservation_id).first()
    guest = db.query(Guest).filter(Guest.id == folio.guest_id).first()
    room = db.query(Room).filter(Room.id == reservation.room_id).first() if reservation else None
    
    return FolioSummary(
        folio_number=folio.folio_number,
        guest_name=f"{guest.first_name} {guest.last_name}" if guest else "Unknown",
        room_number=room.room_number if room else "Unknown",
        subtotal=folio.subtotal,
        tax=folio.tax,
        total=folio.total,
        paid=folio.paid,
        balance=folio.balance
    )

# ==================== GET FOLIO TRANSACTIONS ====================
@router.get("/folios/{folio_id}/transactions", response_model=List[TransactionResponse])
def get_folio_transactions(
    folio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_front_desk)
):
    """
    Get all transactions for a folio
    """
    transactions = db.query(Transaction).filter(Transaction.folio_id == folio_id).order_by(Transaction.created_at).all()
    return transactions