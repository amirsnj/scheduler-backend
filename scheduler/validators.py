from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_date_not_past(date):
    if date < timezone.now().date():
        raise ValidationError("The date should not be for previous days.")