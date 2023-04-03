from django import template
register = template.Library()
@register.filter
def model_name(value):
    return value.__class__.__name__