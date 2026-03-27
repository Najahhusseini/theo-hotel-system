# app/schemas/billing.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TransactionType(str, Enum):
    ROOM_CHARGE = "room_charge"
    SERVICE_CHARGE = "service_charge"
    FOOD_BEVERAGE = "food_beverage"
    SPA = "spa"
    MINI_BAR = "mini_bar"
    PARKING = "parking"
    OTHER = "other"
    PAYMENT = "payment"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    COMPANY_ACCOUNT = "company_account"
    VOUCHER = "voucher"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

# ==================== TRANSACTION SCHEMAS ====================
class TransactionBase(BaseModel):
    transaction_type: TransactionType
    description: str = Field(..., max_length=255)
    amount: float = Field(..., gt=0)
    tax: float = Field(default=0.0, ge=0)
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = Field(default=None, max_length=100)
    external_reference: Optional[str] = Field(default=None, max_length=100)

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    transaction_number: str
    folio_id: int
    processed_by_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ==================== FOLIO SCHEMAS ====================
class FolioBase(BaseModel):
    reservation_id: int
    guest_id: int
    hotel_id: int

class FolioCreate(FolioBase):
    pass

class FolioResponse(FolioBase):
    id: int
    folio_number: str
    subtotal: float
    tax: float
    total: float
    paid: float
    balance: float
    is_open: bool
    is_checked_out: bool
    opened_at: datetime
    closed_at: Optional[datetime]
    transactions: List[TransactionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class FolioSummary(BaseModel):
    folio_number: str
    guest_name: str
    room_number: str
    subtotal: float
    tax: float
    total: float
    paid: float
    balance: float

# ==================== INVOICE SCHEMAS ====================
class InvoiceBase(BaseModel):
    amount: float
    tax: float = 0.0
    due_date: Optional[datetime] = None

class InvoiceCreate(InvoiceBase):
    folio_id: int
    reservation_id: int
    guest_id: int

class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    pdf_url: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: int
    invoice_number: str
    folio_id: int
    reservation_id: int
    guest_id: int
    total: float
    status: InvoiceStatus
    issue_date: datetime
    due_date: Optional[datetime]
    paid_date: Optional[datetime]
    pdf_url: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

# ==================== PAYMENT SCHEMAS ====================
class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class PaymentResponse(BaseModel):
    transaction_id: int
    transaction_number: str
    amount: float
    payment_method: PaymentMethod
    payment_reference: Optional[str]
    new_balance: float
    message: str

# ==================== CHARGE SCHEMAS ====================
class ChargeCreate(BaseModel):
    transaction_type: TransactionType
    description: str
    amount: float = Field(..., gt=0)
    tax: float = Field(default=0.0, ge=0)
    external_reference: Optional[str] = None

# ==================== FOLIO DETAILS ====================
class FolioDetails(BaseModel):
    folio: FolioResponse
    guest: dict
    reservation: dict
    room: dict
    transactions_summary: dict