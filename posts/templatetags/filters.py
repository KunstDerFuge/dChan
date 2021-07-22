from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeString

register = template.Library()


@register.filter(name='parse_styled_text', is_safe=True)
@stringfilter
def parse_styled_text(text: SafeString):
    words = text.split()
    for i in range(len(words)):
        # Check for green text
        if words[i].startswith('> '):
            found_end = False
            for j in range(i, len(words)):
                if words[j].contains('\n'):
                    found_end = True
                    words[i] = '<span class="quote">' + words[i][2:]
                    words[j] = words[j] + '</span>'
                    break
            if not found_end:
                words.append('</span>')

        # Check for styled text
        if words[i].startswith('==') or \
                words[i].startswith("'''") or \
                words[i].startswith("''") or \
                words[i].startswith('__') or \
                words[i].startswith('~~') or \
                words[i.startswith('**')]:
            style = ''
            if words[i].startswith("'''"):
                style = "'''"
            else:
                style = words[i][:2]

            for j in range(i, len(words)):
                if words[j].endswith(style):
                    if style == '==':
                        words[i] = '<span class="header">' + words[i][2:]
                        words[j] = words[j][:-2] + '</span>'
                    elif style == "'''":
                        words[i] = '<strong>' + words[i][3:]
                        words[j] = words[j][:-3] + '</strong>'
                    elif style == "''":
                        words[i] = '<em>' + words[i][2:]
                        words[j] = words[j][:-2] + '</em>'
                    elif style == "__":
                        words[i] = '<u>' + words[i][2:]
                        words[j] = words[j][:-2] + '</u>'
                    elif style == "~~":
                        words[i] = '<s>' + words[i][2:]
                        words[j] = words[j][:-2] + '</s>'
                    elif style == "**":
                        words[i] = '<span class="spoiler">' + words[i][2:]
                        words[j] = words[j][:-2] + '</span>'

    return ' '.join(words)
