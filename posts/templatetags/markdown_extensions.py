import re

from markdown.blockprocessors import BlockProcessor
from markdown.inlinepatterns import SimpleTagInlineProcessor, InlineProcessor
from markdown.extensions import Extension
from markdown import util
import xml.etree.ElementTree as etree


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


class ChanExtensions(Extension):
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
