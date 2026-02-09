from decimal import Decimal
from django.core.exceptions import ValidationError


def validate_amount(value):
    """Validate transaction amounts."""
    if value <= 0:
        raise ValidationError("Amount must be greater than zero")
    
    if value < Decimal('1.00'):
        raise ValidationError("Minimum transaction amount is $1.00")
    
    if value > Decimal('100000.00'):
        raise ValidationError("Maximum transaction amount is $100,000.00")
    
    # Check decimal places
    if value.as_tuple().exponent < -2:
        raise ValidationError("Amount cannot have more than 2 decimal places")
    
    return value


def validate_card_number(card_number):
    """Validate credit card number using Luhn algorithm."""
    card_number = str(card_number).replace(' ', '').replace('-', '')
    
    if not card_number.isdigit():
        raise ValidationError("Card number must contain only digits")
    
    if len(card_number) < 13 or len(card_number) > 19:
        raise ValidationError("Card number must be between 13 and 19 digits")
    
    # Luhn algorithm
    def luhn_checksum(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10
    
    if luhn_checksum(card_number) != 0:
        raise ValidationError("Invalid card number")
    
    return card_number


def validate_cvv(cvv, card_type='visa'):
    """Validate CVV number."""
    cvv = str(cvv)
    
    if not cvv.isdigit():
        raise ValidationError("CVV must contain only digits")
    
    # American Express uses 4 digits, others use 3
    if card_type == 'amex':
        if len(cvv) != 4:
            raise ValidationError("American Express CVV must be 4 digits")
    else:
        if len(cvv) != 3:
            raise ValidationError("CVV must be 3 digits")
    
    return cvv


def sanitize_input(value, max_length=None):
    """Sanitize user input to prevent injection attacks."""
    if not value:
        return value
    
    # Convert to string and strip
    value = str(value).strip()
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '\\', ';', '&', '|']
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    # Apply max length if specified
    if max_length:
        value = value[:max_length]
    
    return value


def validate_pin(pin):
    """Validate PIN number format."""
    pin = str(pin)
    
    if not pin.isdigit():
        raise ValidationError("PIN must contain only digits")
    
    if len(pin) != 4:
        raise ValidationError("PIN must be exactly 4 digits")
    
    return pin
