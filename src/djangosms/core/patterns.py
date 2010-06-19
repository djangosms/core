import re

def keyword(*terms, **kwargs):
    """Return regular expresssion pattern that matches one or more
    keyword terms.

    :param name: The group name for the remaining text (default: ``\"text\"``).
    :param prefix: Keyword prefix character (default: ``\"+\"``).
    :param split: Boolean value whether to split message on prefix character (default: ``True``).

    Examples::

      keyword('reg', 'register')
      keyword('reg', 'register', prefix=\"(+|@)\")

    """

    name = kwargs.pop("name", "text")
    prefix = kwargs.pop("prefix", "+")
    split = kwargs.pop("split", True)

    # longest terms first
    terms = sorted(terms, key=len, reverse=True)

    if split:
        pattern = '^%s' % re.escape(prefix)
    else:
        pattern = '.'

    return '^%s\s*(%s)(\s+(?P<%s>[%s]*)|$)' % (
        re.escape(prefix), '|'.join(terms), name, pattern)

