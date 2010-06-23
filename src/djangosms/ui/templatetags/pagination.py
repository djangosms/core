from django import template
from django.template import RequestContext

register = template.Library()

@register.inclusion_tag('pagination.html')
def pagination(page, req, begin_pages=2, end_pages=2,
               before_current_pages=4, after_current_pages=4):
    # Digg-like pages
    before = max(page.number - before_current_pages - 1, 0)
    after = page.number + after_current_pages

    begin = page.paginator.page_range[:begin_pages]
    middle = page.paginator.page_range[before:after]
    end = page.paginator.page_range[-end_pages:]
    last_page_number = end[-1]

    query_string = req.GET.copy()
    query_string.pop('page', None)
    query_string = query_string.urlencode()

    def collides(firstlist, secondlist):
        """ Returns true if lists collides (have same entries)

        >>> collides([1,2,3,4],[3,4,5,6,7])
        True
        >>> collides([1,2,3,4],[5,6,7])
        False
        """
        return any(item in secondlist for item in firstlist)

    # If middle and end has same entries, then end is what we want
    if collides(middle, end):
        end = range(max(
            last_page_number -
            before_current_pages -
            after_current_pages, 1), last_page_number+1)
        middle = []

    # If begin and middle ranges has same entries, then begin is what we want
    if collides(begin, middle):
        begin = range(1, min(
            before_current_pages +
            after_current_pages,
            last_page_number) + 1)
        middle = []

    # If begin and end has same entries then begin is what we want
    if collides(begin, end):
        begin = range(1, last_page_number+1)
        end = []

    return {
        'page' : page,
        'begin' : begin,
        'middle' : middle,
        'end' : end,
        'query' : query_string
        }
