from django import template

register = template.Library()

# for the rating system - to get the empty stars.
# why there isn't a simpler way to do basic math I dunno

@register.filter
def subtract(value):
    return 5 - value