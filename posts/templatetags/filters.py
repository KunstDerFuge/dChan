from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeString

register = template.Library()


@register.filter(name='replies', is_safe=True)
@stringfilter
def greentext(value: SafeString):
    with_links = value.replace('>>[0-9]+', '<a>test</>')
    return with_links
