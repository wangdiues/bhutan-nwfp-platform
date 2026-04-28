from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def format_price(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal('0')

    if amount == amount.to_integral_value():
        formatted = f'{int(amount):,}'
    else:
        formatted = f'{amount:,.2f}'
    return f'Nu. {formatted}'


@register.filter
def stock_status(value):
    try:
        quantity = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        quantity = Decimal('0')

    if quantity <= 0:
        return 'Out of Stock'
    if quantity <= 10:
        return 'Low Stock'
    return 'In Stock'


@register.filter
def dzongkhag_display(value):
    return str(value or '').replace('_', ' ').replace('-', ' ').title()
