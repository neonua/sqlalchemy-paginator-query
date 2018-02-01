import math
import collections

from sqlalchemy.orm import Query

__version__ = '0.1'


class InvalidPage(Exception):
    pass


class PageNotAnInteger(InvalidPage):
    pass


class EmptyPage(InvalidPage):
    pass


class IsNotQuery(Exception):
    pass


class Paginator:
    def __init__(self, query, per_page_limit, allow_empty_first_page=True):
        self.query = self.validate_query(query)
        self.per_page_limit = int(per_page_limit)
        self.allow_empty_first_page = allow_empty_first_page

    def validate_number(self, page_number):
        """Validate the given 1-based page number."""
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')
        if page_number < 1:
            raise EmptyPage('That page number is less than 1')
        if page_number > self.total_pages:
            if page_number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return page_number

    @staticmethod
    def validate_query(query):
        """Validate the query."""
        if not isinstance(query, Query):
            raise IsNotQuery('Object is not query type')
        return query

    @property
    def total_pages(self):
        """Return the total number of pages."""
        if self.count == 0 and not self.allow_empty_first_page:
            return 0
        return int(math.ceil(self.count / float(self.per_page_limit)))

    @property
    def page_range(self):
        """
        Return a 1-based range of pages for iterating through within
        a template for loop.
        """
        return range(1, self.total_pages + 1)

    @property
    def count(self):
        try:
            return self.query.count()
        except (AttributeError, TypeError):
            return len(self.query)

    def page(self, page_number):
        page_number = self.validate_number(page_number)
        offset_page = (page_number - 1) * self.per_page_limit
        object_list = self.query.offset(offset_page).\
            limit(self.per_page_limit).all()
        return self._get_page(object_list, page_number, self)

    @staticmethod
    def _get_page(*args, **kwargs):
        """
        Return an instance of a single page.
        This hook can be used by subclasses to use an alternative to the
        standard :cls:`Page` object.
        """
        return Page(*args, **kwargs)


class Page(collections.Sequence):
    def __init__(self, object_list, page_number, paginator):
        self.object_list = object_list
        self.page_number = page_number
        self.paginator = paginator

    def __repr__(self):
        return '<Page {page_number} of {total_pages}>'.\
            format(page_number=self.page_number,
                   total_pages=self.paginator.total_pages)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    @property
    def has_prev(self):
        return self.page_number > 1

    @property
    def has_next(self):
        return self.page_number < self.paginator.total_pages

    @property
    def next_page_number(self):
        if self.has_next:
            return self.page_number + 1

    @property
    def prev_page_number(self):
        if self.has_prev:
            return self.page_number - 1
