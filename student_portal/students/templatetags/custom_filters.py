from django import template

register = template.Library()

@register.filter
def get_percentage(value, total):
    """Calculate percentage from value and total"""
    if total == 0:
        return 0
    return int((value / total) * 100)
