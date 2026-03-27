# app/models/billing.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class TransactionType(str, enum.Enum):
    """Type of transaction"""
    ROOM_CHARGE = "room_charge"           # Room rate
    SERVICE_CHARGE = "service_charge"      # Additional services
    FOOD_BEVERAGE = "food_beverage"        # Restaurant/bar
    SPA = "spa"                           # Spa services
    MINI_BAR = "mini_bar"                 # Mini bar charges
    PARKING = "parking"                   # Parking fees
    OTHER = "other"                       # Miscellaneous
    PAYMENT = "payment"                   # Payment received
    REFUND = "refund"                     # Refund issued
    ADJUSTMENT = "adjustment"             # Manual adjustment

class PaymentMethod(str, enum.Enum):
    """Payment methods"""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    COMPANY_ACCOUNT = "company_account"
    VOUCHER = "voucher"

class InvoiceStatus(str, enum.Enum):
    """Invoice status"""
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class Folio(Base):
    """Folio model - guest financial account"""
    __tablename__ = "folios"
    
    id = Column(Integer, primary_key=True, index=True)
    folio_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Foreign keys
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    
    # Financial summary
    subtotal = Column(Float, default=0.0)           # Before tax
    tax = Column(Float, default=0.0)                # Tax amount
    total = Column(Float, default=0.0)              # Subtotal + tax
    paid = Column(Float, default=0.0)               # Amount paid
    balance = Column(Float, default=0.0)            # Total - paid
    
    # Status
    is_open = Column(Boolean, default=True)         # Still active
    is_checked_out = Column(Boolean, default=False) # Guest checked out
    
    # Timestamps
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reservation = relationship("Reservation")
    guest = relationship("Guest")
    hotel = relationship("Hotel")
    transactions = relationship("Transaction", back_populates="folio", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="folio", cascade="all, delete-orphan")

class Transaction(Base):
    """Transaction model - individual charges and payments"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Foreign keys
    folio_id = Column(Integer, ForeignKey("folios.id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)           # Positive for charges, negative for payments
    tax = Column(Float, default=0.0)                 # Tax amount for this transaction
    
    # Payment specific fields (if payment)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    payment_reference = Column(String(100), nullable=True)  # Card last 4, transaction ID, etc.
    
    # Reference to external systems
    external_reference = Column(String(100), nullable=True)  # POS reference, etc.
    
    # Who processed this
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    folio = relationship("Folio", back_populates="transactions")
    processed_by = relationship("User")

class Invoice(Base):
    """Invoice model - billing document"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Foreign keys
    folio_id = Column(Integer, ForeignKey("folios.id"), nullable=False)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    
    # Invoice details
    amount = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    
    # Dates
    issue_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    
    # PDF storage
    pdf_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    folio = relationship("Folio", back_populates="invoices")
    reservation = relationship("Reservation")
    guest = relationship("Guest")