from django import template
from transactions.models import Transaction
from django.utils import timezone

register = template.Library()

@register.filter
def transaction_count(request):
    today = timezone.now().date()
    return Transaction.objects.filter(is_deleted=False, created_at__date=today).count()
