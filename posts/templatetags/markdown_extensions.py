import html
import xml.etree.ElementTree as etree

from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor, ParagraphProcessor
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor, InlineProcessor


class CustomParagraphProcessor(ParagraphProcessor):
    def run(self, parent, blocks):
        block = blocks.pop(0)
        if block.strip():
            # Not a blank block. Add to parent, otherwise throw it away.
            if self.parser.state.isstate('list'):
                # The parent is a tight-list.
                #
                # Check for any children. This will likely only happen in a
                # tight-list when a header isn't followed by a blank line.
                # For example:
                #
                #     * # Header
                #     Line 2 of list item - not part of header.
                sibling = self.lastChild(parent)
                if sibling is not None:
                    # Insetrt after sibling.
                    if sibling.tail:
                        sibling.tail = '{}\n{}'.format(sibling.tail, block)
                    else:
                        sibling.tail = '\n%s' % block
                else:
                    # Append to parent.text
                    if parent.text:
                        parent.text = '{}\n{}'.format(parent.text, block)
                    else:
                        parent.text = block.lstrip()
            else:
                # Create a regular paragraph
                p = etree.SubElement(parent, 'p')
                p.attrib = {'class': 'body-line'}
                p.text = block.lstrip()


class SimpleSpanTagInlineProcessor(InlineProcessor):
    """
    Return element of type `span` with a text attribute of group(1)
    of a Pattern.
    """

    def __init__(self, pattern, attr):
        InlineProcessor.__init__(self, pattern)
        self.tag = 'span'
        self.attr = {'class': attr}

    def handleMatch(self, m, data):  # pragma: no cover
        el = etree.Element(self.tag)
        el.attrib = self.attr
        el.text = m.group(1)
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
    Return a link to the >>post from the original processed link
    """

    def __init__(self, pattern, links):
        InlineProcessor.__init__(self, pattern)
        self.links = links

    def handleMatch(self, m, data):
        el = etree.Element('a')
        el.text = m.group(1)
        link_text = html.unescape(m.group(1))

        if link_text in self.links:
            el.attrib = {'href': f'{self.links[link_text]}'}
            return el, m.start(0), m.end(0)
        else:
            return None, None, None


class ChanExtensions(Extension):
    def __init__(self, links):
        self.links = links

    def extendMarkdown(self, md):
        block_parser = BlockParser(md)
        md.parser.blockprocessors.deregister('quote')
        md.parser.blockprocessors.deregister('indent')
        md.parser.blockprocessors.deregister('code')
        md.parser.blockprocessors.deregister('hashheader')
        md.parser.blockprocessors.deregister('setextheader')
        md.parser.blockprocessors.deregister('hr')
        md.parser.blockprocessors.deregister('reference')
        md.parser.blockprocessors.deregister('paragraph')
        md.parser.blockprocessors.register(CustomParagraphProcessor(block_parser), 'paragraph', 10)
        md.inlinePatterns.register(SimpleSpanTagInlineProcessor(r'&gt; (.*)($|\n)', 'quote'), 'quote', 175)
        md.inlinePatterns.register(SimpleTagInlineProcessor(r"()&#x27;&#x27;&#x27;(.*?)&#x27;&#x27;&#x27;", 'strong'), 'strong', 175)
        md.inlinePatterns.register(SimpleTagInlineProcessor(r"()&#x27;&#x27;(.*?)&#x27;&#x27;", 'em'), 'em', 175)
        md.inlinePatterns.register(SimpleSpanTagInlineProcessor(r'==(.*?)==', 'heading'), 'heading', 175)
        md.inlinePatterns.register(
            InlinePostLinkProcessor(r'(&gt;&gt;[0-9]+|&gt;&gt;&gt;/[a-zA-Z]+/[0-9]+)', self.links), 'post_link',
            175)
        md.inlinePatterns.register(InlineEchoesProcessor(r'(\(\(\(.{1,25}\)\)\))'), 'triple_parentheses', 175)
