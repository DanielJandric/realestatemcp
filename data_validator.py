"""
Data validation utilities for real estate data
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
import pandas as pd

class ValidationResult:
    """Result of a validation check"""
    def __init__(self, valid: bool, errors: List[str] = None):
        self.valid = valid
        self.errors = errors or []
    
    def __bool__(self):
        return self.valid
    
    def __repr__(self):
        if self.valid:
            return "✅ Valid"
        return f"❌ Invalid: {', '.join(self.errors)}"

class DataValidator:
    """Validate real estate data before insertion"""
    
    @staticmethod
    def validate_email(email: Optional[str]) -> ValidationResult:
        """Validate email format"""
        if not email or pd.isna(email):
            return ValidationResult(True)  # Nullable
        
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        if re.match(pattern, str(email)):
            return ValidationResult(True)
        return ValidationResult(False, ["Invalid email format"])
    
    @staticmethod
    def validate_phone(phone: Optional[str]) -> ValidationResult:
        """Validate phone number format"""
        if not phone or pd.isna(phone):
            return ValidationResult(True)  # Nullable
        
        # Allow various formats: +41 XX XXX XX XX, 0XX XXX XX XX, etc.
        phone_str = str(phone).replace(' ', '').replace('-', '').replace('.', '')
        if re.match(r'^(\+41|0041|0)[0-9]{9}$', phone_str):
            return ValidationResult(True)
        return ValidationResult(False, ["Invalid Swiss phone format"])
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "value") -> ValidationResult:
        """Validate that a number is positive"""
        if value is None or pd.isna(value):
            return ValidationResult(True)  # Nullable
        
        try:
            num = float(value)
            if num >= 0:
                return ValidationResult(True)
            return ValidationResult(False, [f"{field_name} must be non-negative"])
        except (ValueError, TypeError):
            return ValidationResult(False, [f"{field_name} must be a number"])
    
    @staticmethod
    def validate_date_range(start_date: Any, end_date: Any) -> ValidationResult:
        """Validate that end_date is after start_date"""
        if not start_date or not end_date or pd.isna(start_date) or pd.isna(end_date):
            return ValidationResult(True)  # Nullable
        
        try:
            if isinstance(start_date, str):
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                start = start_date
            
            if isinstance(end_date, str):
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                end = end_date
            
            if end >= start:
                return ValidationResult(True)
            return ValidationResult(False, ["End date must be after start date"])
        except Exception as e:
            return ValidationResult(False, [f"Invalid date format: {e}"])
    
    @staticmethod
    def validate_non_empty_string(value: Any, field_name: str = "value") -> ValidationResult:
        """Validate that a string is not empty"""
        if not value or pd.isna(value):
            return ValidationResult(False, [f"{field_name} cannot be empty"])
        
        if isinstance(value, str) and value.strip():
            return ValidationResult(True)
        return ValidationResult(False, [f"{field_name} must be a non-empty string"])
    
    @staticmethod
    def validate_status(status: str, valid_statuses: List[str]) -> ValidationResult:
        """Validate that status is in allowed list"""
        if not status or pd.isna(status):
            return ValidationResult(True)  # Nullable
        
        if str(status).lower() in [s.lower() for s in valid_statuses]:
            return ValidationResult(True)
        return ValidationResult(False, [f"Invalid status. Must be one of: {', '.join(valid_statuses)}"])
    
    @classmethod
    def validate_property(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate property data"""
        errors = []
        
        # Name is required
        result = cls.validate_non_empty_string(data.get('name'), 'name')
        if not result:
            errors.extend(result.errors)
        
        return ValidationResult(len(errors) == 0, errors)
    
    @classmethod
    def validate_unit(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate unit data"""
        errors = []
        
        # Surface area must be positive if provided
        result = cls.validate_positive_number(data.get('surface_area'), 'surface_area')
        if not result:
            errors.extend(result.errors)
        
        # Rooms must be positive if provided
        result = cls.validate_positive_number(data.get('rooms'), 'rooms')
        if not result:
            errors.extend(result.errors)
        
        return ValidationResult(len(errors) == 0, errors)
    
    @classmethod
    def validate_tenant(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate tenant data"""
        errors = []
        
        # Name is required
        result = cls.validate_non_empty_string(data.get('name'), 'name')
        if not result:
            errors.extend(result.errors)
        
        # Email format
        result = cls.validate_email(data.get('email'))
        if not result:
            errors.extend(result.errors)
        
        # Phone format
        result = cls.validate_phone(data.get('phone'))
        if not result:
            errors.extend(result.errors)
        
        return ValidationResult(len(errors) == 0, errors)
    
    @classmethod
    def validate_lease(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate lease data"""
        errors = []
        
        # Rent must be non-negative
        result = cls.validate_positive_number(data.get('rent_net'), 'rent_net')
        if not result:
            errors.extend(result.errors)
        
        # Charges must be non-negative
        result = cls.validate_positive_number(data.get('charges'), 'charges')
        if not result:
            errors.extend(result.errors)
        
        # Deposit must be non-negative
        result = cls.validate_positive_number(data.get('deposit'), 'deposit')
        if not result:
            errors.extend(result.errors)
        
        # Date range validation
        result = cls.validate_date_range(data.get('start_date'), data.get('end_date'))
        if not result:
            errors.extend(result.errors)
        
        # Status validation
        valid_statuses = ['active', 'terminated', 'pending', 'draft']
        result = cls.validate_status(data.get('status'), valid_statuses)
        if not result:
            errors.extend(result.errors)
        
        return ValidationResult(len(errors) == 0, errors)
    
    @classmethod
    def validate_dispute(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate dispute data"""
        errors = []
        
        # Amount must be non-negative
        result = cls.validate_positive_number(data.get('amount'), 'amount')
        if not result:
            errors.extend(result.errors)
        
        # Status validation
        valid_statuses = ['open', 'in_progress', 'resolved', 'closed', 'pending']
        result = cls.validate_status(data.get('status'), valid_statuses)
        if not result:
            errors.extend(result.errors)
        
        return ValidationResult(len(errors) == 0, errors)
    
    @classmethod
    def validate_incident(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate incident data"""
        errors = []
        
        # Status validation
        valid_statuses = ['reported', 'investigating', 'resolved', 'closed', 'insurance_claim']
        result = cls.validate_status(data.get('status'), valid_statuses)
        if not result:
            errors.extend(result.errors)
        
        return ValidationResult(len(errors) == 0, errors)
    
    @classmethod
    def validate_maintenance(cls, data: Dict[str, Any]) -> ValidationResult:
        """Validate maintenance data"""
        errors = []
        
        # Cost must be non-negative
        result = cls.validate_positive_number(data.get('cost'), 'cost')
        if not result:
            errors.extend(result.errors)
        
        # Date range validation
        result = cls.validate_date_range(data.get('start_date'), data.get('end_date'))
        if not result:
            errors.extend(result.errors)
        
        return ValidationResult(len(errors) == 0, errors)

def generate_data_quality_report(supabase_client) -> Dict[str, Any]:
    """Generate a comprehensive data quality report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'issues': []
    }
    
    # Check for tenants without valid emails
    tenants = supabase_client.table("tenants").select("id, name, email").execute().data
    invalid_emails = []
    for tenant in tenants:
        if tenant.get('email'):
            result = DataValidator.validate_email(tenant['email'])
            if not result:
                invalid_emails.append({
                    'id': tenant['id'],
                    'name': tenant['name'],
                    'email': tenant['email']
                })
    
    if invalid_emails:
        report['issues'].append({
            'category': 'Invalid Emails',
            'count': len(invalid_emails),
            'examples': invalid_emails[:5]
        })
    
    # Check for leases with invalid dates
    leases = supabase_client.table("leases").select("id, start_date, end_date").execute().data
    invalid_dates = []
    for lease in leases:
        result = DataValidator.validate_date_range(lease.get('start_date'), lease.get('end_date'))
        if not result:
            invalid_dates.append({
                'id': lease['id'],
                'start_date': lease.get('start_date'),
                'end_date': lease.get('end_date')
            })
    
    if invalid_dates:
        report['issues'].append({
            'category': 'Invalid Date Ranges',
            'count': len(invalid_dates),
            'examples': invalid_dates[:5]
        })
    
    # Check for negative amounts
    leases_negative = [l for l in leases if (l.get('rent_net') or 0) < 0 or (l.get('charges') or 0) < 0]
    if leases_negative:
        report['issues'].append({
            'category': 'Negative Rent/Charges',
            'count': len(leases_negative),
            'examples': [{'id': l['id']} for l in leases_negative[:5]]
        })
    
    report['total_issues'] = len(report['issues'])
    report['status'] = 'CLEAN' if report['total_issues'] == 0 else 'ISSUES_FOUND'
    
    return report
