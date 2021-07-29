from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import markdown as md
from .markdown_extensions import ChanExtensions

register = template.Library()


@register.filter(name='markdown')
@stringfilter
def markdown(text, links):
    return mark_safe(md.markdown(text, extensions=['nl2br', ChanExtensions(links)]))


@register.filter(name='get_archive_link')
@stringfilter
def get_archive_link(path):
    parts = path.split('/')[1:]
    print(parts)
    new_path = '/'.join(parts[1:])
    site = {'8chan': 'https://8ch.net', '8kun': 'https://8kun.top'}
    return f'https://archive.is/{site[parts[0]]}/{new_path}'
