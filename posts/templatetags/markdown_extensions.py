import xml.etree.ElementTree as etree

from django.core.exceptions import ObjectDoesNotExist
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor, InlineProcessor
from posts.models import Post

class SimpleSpanTagInlineProcessor(InlineProcessor):
    """
    Return element of type `span` with a text attribute of group(2)
    of a Pattern.
    """

    def __init__(self, pattern, attr):
        InlineProcessor.__init__(self, pattern)
        self.tag = 'span'
        self.attr = {'class': attr}

    def handleMatch(self, m, data):  # pragma: no cover
        el = etree.Element(self.tag)
        el.attrib = self.attr
        el.text = m.group(2)
        return el, m.start(0), m.end(0)


class InlineEchoesProcessor(InlineProcessor):
    """
    Return a link to the Wikipedia page on the triple parentheses
    """

    def handleMatch(self, m, data):
        el = etree.Element('a')
        el.text = m.group(1)
        el.attrib = {
            'href': 'https://en.wikipedia.org/wiki/Triple_parentheses',
            'style': 'text-decoration: inherit; color: inherit;'
        }
        return el, m.start(0), m.end(0)


class InlinePostLinkProcessor(InlineProcessor):
    """
    Return a link to the >>post, if archived
    """

    def __init__(self, pattern, links):
        InlineProcessor.__init__(self, pattern)
        self.links = links

    def handleMatch(self, m, data):
        el = etree.Element('a')
        el.text = '>>' + m.group(1)
        post_no = m.group(1)

        if post_no in self.links:
            el.attrib = {'href': self.links[post_no]}
            return el, m.start(0), m.end(0)
        else:
            return None, None, None


class ChanExtensions(Extension):
    def __init__(self, url):
        self.url = url

    def extendMarkdown(self, md):
        md.parser.blockprocessors.deregister('quote')
        md.parser.blockprocessors.deregister('indent')
        md.parser.blockprocessors.deregister('code')
        md.parser.blockprocessors.deregister('hashheader')
        md.parser.blockprocessors.deregister('setextheader')
        md.parser.blockprocessors.deregister('hr')
        md.parser.blockprocessors.deregister('reference')
        md.inlinePatterns.register(SimpleSpanTagInlineProcessor(r'()> (.*)($|\n)', 'quote'), 'quote', 175)
        md.inlinePatterns.register(SimpleTagInlineProcessor(r"()'''(.*?)'''", 'strong'), 'strong', 175)
        md.inlinePatterns.register(SimpleTagInlineProcessor(r"()''(.*?)''", 'em'), 'em', 175)
        md.inlinePatterns.register(SimpleSpanTagInlineProcessor(r'()==(.*?)==', 'heading'), 'heading', 175)
        md.inlinePatterns.register(InlinePostLinkProcessor(r'>>([0-9]+)', self.url), 'post_link', 175)
        md.inlinePatterns.register(InlineEchoesProcessor(r'(\(\(\(.{1,20}\)\)\))'), 'triple_parentheses', 175)
