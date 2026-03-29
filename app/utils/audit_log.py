# app/utils/audit_log.py
import logging
from datetime import datetime
from typing import Optional
import json
import os

# Create audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create audit log file handler
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(f"{log_dir}/audit.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
audit_logger.addHandler(file_handler)

class AuditLogger:
    """
    Audit logging for tracking all sensitive actions.
    Essential for compliance and security investigations.
    """
    
    @staticmethod
    def log_action(
        user_id: Optional[int],
        username: Optional[str],
        action: str,
        resource: str,
        resource_id: Optional[int],
        details: dict,
        ip_address: str,
        user_agent: str,
        status: str = "success"
    ):
        """
        Log an audit entry for sensitive actions.
        
        Sensitive actions include:
        - Login attempts (success/failure)
        - User creation/deletion
        - Role changes
        - Reservation modifications
        - Payment processing
        - Check-in/out
        - Room status changes
        - Maintenance requests
        - Data exports
        """
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": status
        }
        
        audit_logger.info(json.dumps(audit_entry))
        
        # Also print to console for development
        print(f"[AUDIT] {action} by {username or 'anonymous'} on {resource}: {details}")
    
    @staticmethod
    def log_login_attempt(
        username: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        reason: Optional[str] = None
    ):
        """Log login attempts (critical for security)"""
        AuditLogger.log_action(
            user_id=None,
            username=username,
            action="login_attempt",
            resource="auth",
            resource_id=None,
            details={
                "success": success,
                "reason": reason
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failed"
        )
    
    @staticmethod
    def log_user_management(
        user_id: int,
        username: str,
        action: str,  # created, updated, deleted, role_changed
        target_user_id: int,
        target_username: str,
        changes: dict,
        ip_address: str,
        user_agent: str
    ):
        """Log user management actions"""
        AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action=action,
            resource="user",
            resource_id=target_user_id,
            details={
                "target_username": target_username,
                "changes": changes
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_financial_action(
        user_id: int,
        username: str,
        action: str,  # payment_processed, refund_issued, invoice_created
        resource: str,  # reservation, folio, invoice
        resource_id: int,
        amount: float,
        details: dict,
        ip_address: str,
        user_agent: str
    ):
        """Log financial transactions (critical for audit)"""
        AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details={
                "amount": amount,
                **details
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_data_export(
        user_id: int,
        username: str,
        export_type: str,  # guests, reservations, financial
        filters: dict,
        ip_address: str,
        user_agent: str
    ):
        """Log data exports (GDPR compliance)"""
        AuditLogger.log_action(
            user_id=user_id,
            username=username,
            action="data_export",
            resource=export_type,
            resource_id=None,
            details={"filters": filters},
            ip_address=ip_address,
            user_agent=user_agent
        )