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


def hex_to_rgb(hex_):
    r = int(hex_[:2], 16) / 255
    g = int(hex_[2:4], 16) / 255
    b = int(hex_[4:], 16) / 255
    return r, g, b


def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))


@register.filter(name='contrast_text')
@stringfilter
def contrast_text(bg_color):
    if bg_color.startswith('#'):
        bg_color = bg_color[1:]
    r, g, b = hex_to_rgb(bg_color)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if luminance > 0.65:
        return 'black'
    return 'white'


@register.filter(name='pastelize')
@stringfilter
def pastelize(poster_hash):
    if poster_hash == '000000':
        return '#000000'
    r, g, b = hex_to_rgb(poster_hash)
    r += (1 - r) / 2
    g += (1 - g) / 2
    b += (1 - b) / 2
    return rgb_to_hex(r, g, b)

