import inspect

from django.core.paginator import Paginator, Page
# Source: https://github.com/jaddison/django-simple-elasticsearch/blob/0.9.11/simple_elasticsearch/forms.py
from django.utils.functional import cached_property
from django.utils.inspect import method_has_no_args


class DSEPaginator(Paginator):
    """
    Override Django's built-in Paginator class to take in a count/total number of items;
    Elasticsearch provides the total as a part of the query results, so we can minimize hits.
    """
    def __init__(self, *args, **kwargs):
        super(DSEPaginator, self).__init__(*args, **kwargs)
        self._count = self.object_list.hits.total

    def page(self, number):
        # this is overridden to prevent any slicing of the object_list - Elasticsearch has
        # returned the sliced data already.
        number = self.validate_number(number)
        return Page(self.object_list, number, self)

    @cached_property
    def count(self):
        """Return the total number of objects, across all pages."""
        return self._count['value']
