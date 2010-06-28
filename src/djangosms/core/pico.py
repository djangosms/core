import datetime
import itertools

from string import digits as digit_chars
from string import ascii_letters

from picoparse import choice
from picoparse import fail
from picoparse import many
from picoparse import many1
from picoparse import n_of
from picoparse import one_of
from picoparse import not_one_of
from picoparse import optional
from picoparse import partial
from picoparse import run_parser
from picoparse import satisfies
from picoparse import sep
from picoparse import sep1
from picoparse import tri
from picoparse import NoMatch
from picoparse.text import caseless_string
from picoparse.text import lexeme
from picoparse.text import whitespace
from picoparse.text import whitespace1

comma = partial(one_of, ',')
dot = partial(one_of, '.')
hash = partial(one_of, '#')
not_comma = partial(not_one_of, ',')
digit = partial(one_of, digit_chars)
digits = partial(many1, digit)

_unit_days_multiplier = {
    'd': 1,
    'w': 7,
    'm': 30,
    'y': 365,
    }

_short_months = [datetime.date(1900, i, 1).strftime('%b') for i in range(1, 13)]
_long_months = [datetime.date(1900, i, 1).strftime('%B') for i in range(1, 13)]

_date_format_mapping = {
    '-': partial(one_of, '-'),
    ',': partial(one_of, ','),
    '.': partial(one_of, '.'),
    ' ': partial(one_of, ' '),
    '/': partial(one_of, '/'),
    'Y': partial(n_of, digit, 4),
    'y': partial(n_of, digit, 2),
    'm': digits,
    'd': digits,
    'b': partial(choice, *map(tri, map(partial(partial, caseless_string), _short_months))),
    'B': partial(choice, *map(tri, map(partial(partial, caseless_string), _long_months))),
    }

def _parse_date_format(date_format):
    tokens = tuple(date_format.replace('%', ''))
    parsers = map(tri, map(_date_format_mapping.get, tokens))
    date_string = "".join(itertools.chain(*[parser() for parser in parsers]))
    try:
        return datetime.datetime.strptime(date_string, date_format)
    except:
        fail()

def wrap(name):
    """Decorates a parse-function.

    :param name: Name of the keyword argument that holds the parser input string.
    """

    def decorator(parser):
        def parse(*args, **kwargs):
            try:
                text = kwargs.pop(name) or ("\n", )
            except KeyError:
                raise KeyError(
                    "Expected key: '%s' in arguments (got: %s)." % (
                        name, repr(kwargs)))

            try:
                result, remaining = run_parser(partial(parser, *args, **kwargs), text)
            except NoMatch:
                return None
            except Exception, exc: # pragma: NOCOVER
                # backwards compatible with older version of
                # picoparse; this is equivalent to not
                # matching
                if 'Commit / cut called' in unicode(exc):
                    return None
                raise

            return result

        decorator.__doc__ = parser.__doc__
        return parse
    return decorator

def parse(parser, text):
    return "".join(run_parser(parser, tuple(text))[0])

def identifier(first=partial(one_of, ascii_letters),
               consecutive=partial(one_of, ascii_letters + digit_chars + '_'),
               must_contain=set(digit_chars)):
    """Expects a letter followed by one or more alphanumerical
    characters. If ``must_contain`` is given, the following letters
    must include one from this set.

    The default option is to expect a letter followed by a number of
    letters and digits, but with a requirement of at least one digit
    (this allows an easy distinction between names and identifiers).

    >>> parse(identifier, 'abc123')
    'abc123'
    >>> parse(identifier, 'abc') # doctest: +ELLIPSIS
    Traceback (most recent call last):
     ...
    NoMatch: ...
    >>> parse(partial(identifier, must_contain=None), 'abc')
    'abc'
    """

    result = []
    if first is not None:
        result.append(first())

    if must_contain is None:
        chars = many(consecutive)
    else:
        chars = many1(partial(choice, consecutive, partial(one_of, must_contain)))
        if not set(chars) & must_contain:
            fail()

    result.extend(chars)
    return result

def identifiers(**kwargs):
    """Parse multiple identifiers, separated by whitespace and/or
    comma.

    >>> run_parser(identifiers, 'abc123 def456')[0]
    ['abc123', 'def456']

    """

    term = partial(identifier, **kwargs)
    return map(partial("".join),
               sep(term, partial(many1, partial(one_of, ' ,'))))

def ids(**kwargs):
    """Parse IDs (alphanumerical identifiers).

    >>> run_parser(ids, 'abc123 def456')[0]
    ['abc123', 'def456']

    >>> run_parser(ids, '12ab65')[0]
    ['12ab65']
    """

    return identifiers(first=None)

def separator(parser=comma):
    """Expects a comma separation.

    >>> parse(separator, ', ')
    ','
    >>> parse(separator, ' ,')
    ','
    """

    return lexeme(parser)

def date(formats=("%m/%d/%Y",)):
    """Parses a date using one of the supplied formats.

    To integrate with Django's date format settings, pass in the
    ``DATE_INPUT_FORMATS`` setting. The default settings is defined in
    :mod:`django.conf.global_settings` as::

      DATE_INPUT_FORMATS = (
          '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', # '2006-10-25', '10/25/2006', '10/25/06'
          '%b %d %Y', '%b %d, %Y',            # 'Oct 25 2006', 'Oct 25, 2006'
          '%d %b %Y', '%d %b, %Y',            # '25 Oct 2006', '25 Oct, 2006'
          '%B %d %Y', '%B %d, %Y',            # 'October 25 2006', 'October 25, 2006'
          '%d %B %Y', '%d %B, %Y',            # '25 October 2006', '25 October, 2006'
      )

    To use this setting, wrap the function like this:

    >>> from django.conf import settings
    >>> date = partial(date, formats=settings.DATE_INPUT_FORMATS)

    The standard settings enables a wide set of input formats; we
    demonstrate some of them here:

    >>> run_parser(date, '12/31/1999')[0].isoformat()
    '1999-12-31T00:00:00'
    >>> run_parser(date, 'December 31, 1999')[0].isoformat()
    '1999-12-31T00:00:00'
    >>> run_parser(date, '12/31/99')[0].isoformat()
    '1999-12-31T00:00:00'
    """

    parsers = [partial(_parse_date_format, f) for f in formats]
    return choice(*map(tri, parsers))

def timedelta():
    """Parses a time quantity into a :mod:`datetime.timedelta` instance.

    >>> run_parser(timedelta, '7 days')[0].days
    7
    >>> run_parser(timedelta, '7 DayS')[0].days
    7
    >>> run_parser(timedelta, '7d')[0].days
    7
    >>> run_parser(timedelta, '1w')[0].days
    7
    >>> run_parser(timedelta, '2m')[0].days
    60
    >>> run_parser(timedelta, '6 months')[0].days
    180
    >>> run_parser(timedelta, '1 year')[0].days
    365
    >>> run_parser(timedelta, '2 yrs')[0].days // 2
    365
    """

    number = int("".join(digits()))

    def unit():
        whitespace()
        unit = one_of_strings(
            'day',
            'week', 'wk',
            'month', 'mo',
            'year', 'yr',
            'd',
            'w',
            'm',
            'y', )[0]
        optional(partial(one_of, 'sS'), None)
        return unit

    multiplier = _unit_days_multiplier[unit().lower()]
    return datetime.timedelta(days=multiplier*number)

def floating():
    """Parses a floating point number.

    >>> parse(floating, '123')
    '123'
    >>> parse(floating, '123.0')
    '123.0'
    >>> parse(floating, '123,0')
    '123.0'
    >>> parse(floating, '.123')
    '.123'
    >>> parse(floating, '123.')
    '123.'

    """

    number = optional(digits, [])
    if optional(partial(choice, comma, dot), None):
        number += "."
    number += optional(digits, [])
    return number

def name():
    """Parses one or more names separated by whitespace, and
    concatenates with a single space.

    >>> parse(name, 'John')
    'John'

    >>> parse(name, 'John Smith')
    'John Smith'

    >>> parse(name, 'John, Smith')
    'John'

    >>> parse(name, 'John Smith ')
    'John Smith'
    """

    names = map(partial("".join), sep1(
        partial(many, partial(satisfies, lambda l: l and l.isalpha())), whitespace1))

    name = " ".join(names).strip()
    if not name:
        fail()

    return name

def one_of_strings(*strings):
    """Parses one of the strings provided, caseless.

    >>> parse(partial(one_of_strings, 'abc', 'def'), 'abc')
    'abc'
    >>> parse(partial(one_of_strings, 'abc', 'def'), 'def')
    'def'
    """

    return choice(*map(tri, map(partial(partial, caseless_string), strings)))

def tag():
    """Parse a single tag, optionally prefixed by a hash mark
    (``'#'``).
    """

    optional(hash, None)
    return many1(partial(one_of, ascii_letters))

def tags():
    """Parse one or more tags, each separated by whitespace and/or a
    comma.

    >>> run_parser(tags, 'abc, def')[0]
    ['abc', 'def']
    >>> run_parser(tags, '#abc #def')[0]
    ['abc', 'def']
    """

    return map(partial("".join), sep(tag, partial(many1, partial(one_of, ' ,'))))

