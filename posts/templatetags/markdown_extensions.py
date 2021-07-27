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


class InlinePostLinkProcessor(InlineProcessor):
    """
    Return a link to the >>post, if archived
    """

    def __init__(self, pattern, url):
        InlineProcessor.__init__(self, pattern)
        self.tag = 'a'
        self.current_url = url

    def handleMatch(self, m, data):
        el = etree.Element(self.tag)
        el.text = '>>' + m.group(1)
        platform = self.current_url.split('/')[-4]
        board = self.current_url.split('/')[-3]
        post_no = m.group(1)
        # Does such a Post exist on this board?
        try:
            post = Post.objects.get(platform=platform, board=board, post_id=post_no)
        except Exception:
            post = None
        if post is not None:
            el.attrib = {'href': f'/{platform}/{board}/res/{post.thread_id}.html#{post_no}'}
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
