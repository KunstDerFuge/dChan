import hashlib
import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import markdown as md
from .markdown_extensions import ChanExtensions
from ..models import Board, Platform

register = template.Library()


@register.filter(name='markdown')
@stringfilter
def markdown(text, links):
    pattern = re.compile(r'(\n\ {1,4}\n)')  # Match two newlines separated by 1-4 spaces
    text = pattern.sub('\n\n', text)
    text = '\n\n'.join(text.split('\n'))
    text = text.replace('\n\n\n\n', '\n\n&nbsp;\n\n')
    return mark_safe(md.markdown(text, extensions=[ChanExtensions(links)]))


@register.filter(name='get_archive_link')
@stringfilter
def get_archive_link(path):
    parts = path.split('/')[1:]
    new_path = '/'.join(parts)
    return f'https://archive.is/https://8kun.top/{new_path}'


def hex_to_rgb(hex_):
    try:
        r = int(hex_[:2], 16) / 255
        g = int(hex_[2:4], 16) / 255
        b = int(hex_[4:], 16) / 255
        return r, g, b
    except Exception:
        return 0, 0, 0


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
    if len(poster_hash) > 6:  # 4chan hash
        hash_bytes = poster_hash.encode()
        hash_obj = hashlib.sha1(hash_bytes)
        poster_hash = hash_obj.hexdigest()[-6:]  # Take last 6 chars
    if poster_hash == '000000':
        return '#000000'
    r, g, b = hex_to_rgb(poster_hash)
    r += (1 - r) / 2
    g += (1 - g) / 2
    b += (1 - b) / 2
    return rgb_to_hex(r, g, b)


@register.filter(name='get_cracked_pass')
@stringfilter
def get_cracked_pass(tripcode):
    tripcode = tripcode.strip('!')
    cracked = {
        'ITPb.qbhqo': 'Matlock',
        'UW.yye1fxo': 'M@tlock!',
        'xowAT4Z3VQ': 'Freed@m-',
        '2jsTvXXmXs': 'F!ghtF!g',
        '4pRcUA0lBE': 'NowC@mes',
        'CbboFOtcZs': 'StoRMkiL',
        'A6yxsPKia.': 'WeAReQ@Q'
    }
    if tripcode in cracked:
        return cracked[tripcode]
    return ''


@register.filter(name='reply_string')
@stringfilter
def reply_string(post_no):
    return f'>>{post_no[-4:]}'
