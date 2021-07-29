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
    new_path = '/'.join(parts[1:])
    site = {'8chan': 'https://8ch.net', '8kun': 'https://8kun.top'}
    return f'https://archive.is/{site[parts[0]]}/{new_path}'


@register.filter(name='contrast_text')
@stringfilter
def contrast_text(bg_color):
    r = int(bg_color[:2], 16) / 255
    g = int(bg_color[2:4], 16) / 255
    b = int(bg_color[4:], 16) / 255
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if luminance > 0.6:
        return 'black'
    return 'white'
