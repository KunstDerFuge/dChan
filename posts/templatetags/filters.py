from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import markdown as md
from .markdown_extensions import ChanExtensions

register = template.Library()


@register.filter(name='markdown')
@stringfilter
def markdown(text, url):
    return mark_safe(md.markdown(text, extensions=['nl2br', ChanExtensions(url)]))
