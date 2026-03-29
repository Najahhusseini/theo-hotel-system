\# THEO - Role-Based Access Control (RBAC) Reference



\## Role Hierarchy



| Role | Level | Color | Description |

|------|-------|-------|-------------|

| Super Admin | 100 | 🔴 Red | Full system control |

| Hotel Manager | 80 | 🟠 Orange | Hotel-level management |

| Accounting | 70 | 🟡 Yellow | Financial operations |

| Front Desk | 50 | 🟢 Green | Guest operations |

| Housekeeping | 30 | 🔵 Blue | Room cleaning |

| Maintenance | 20 | 🟣 Purple | Issue tracking |



\## Permission Matrix



\### Hotel Management

| Action | Admin | Manager | Front Desk | Housekeeping | Maintenance | Accounting |

|--------|-------|---------|------------|--------------|-------------|------------|

| View Hotels | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Create Hotel | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

| Update Hotel | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

| Delete Hotel | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |



\### Room Management

| Action | Admin | Manager | Front Desk | Housekeeping | Maintenance | Accounting |

|--------|-------|---------|------------|--------------|-------------|------------|

| View Rooms | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

| Create Room | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

| Update Room | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

| Update Room Status | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

| Delete Room | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |



\### Guest Management (CRM)

| Action | Admin | Manager | Front Desk | Housekeeping | Maintenance | Accounting |

|--------|-------|---------|------------|--------------|-------------|------------|

| View Guests | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

| Create Guest | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Update Guest | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Delete Guest | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

| View Guest History | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |



\### Reservation Management

| Action | Admin | Manager | Front Desk | Housekeeping | Maintenance | Accounting |

|--------|-------|---------|------------|--------------|-------------|------------|

| View Reservations | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

| Create Reservation | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Update Reservation | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Check-in | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Check-out | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Cancel Reservation | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

| Delete Reservation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |



\### Staff Management

| Action | Admin | Manager | Front Desk | Housekeeping | Maintenance | Accounting |

|--------|-------|---------|------------|--------------|-------------|------------|

| View Staff | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

| Create Staff | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

| Update Staff | ✅ | ✅\* | ❌ | ❌ | ❌ | ❌ |

| Delete Staff | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |



\*Manager can only update staff in their hotel



\### Financial Operations

| Action | Admin | Manager | Front Desk | Housekeeping | Maintenance | Accounting |

|--------|-------|---------|------------|--------------|-------------|------------|

| View Billing | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

| Process Payment | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |

| View Reports | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |

| Generate Invoice | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |



\## Test Credentials



| Role | Username | Password |

|------|----------|----------|

| Super Admin | admin | Admin123! |

| Hotel Manager | manager | Manager123! |

| Front Desk | frontdesk | Front123! |

| Housekeeping | housekeeping | House123! |

| Maintenance | maintenance | Maint123! |

| Accounting | accounting | Acct123! |



\## API Endpoints by Role



\### Public (No Authentication)

\- POST /api/v1/auth/login



\### Super Admin Only

\- POST /api/v1/auth/register

\- DELETE /api/v1/users/{id}

\- All hotel deletion endpoints



\### Hotel Manager+

\- All hotel management (except deletion)

\- Staff management within their hotel

\- All operational reports



\### Front Desk+

\- Guest search and management

\- Reservation creation and modification

\- Check-in/check-out operations

\- Room status viewing



\### Housekeeping+

\- Room status updates

\- View assigned tasks

\- Mark tasks complete



\### Maintenance+

\- View maintenance requests

\- Update request status

\- Log work completed



\### Accounting+

\- View all financial data

\- Process payments

\- Generate invoices

\- View reports

