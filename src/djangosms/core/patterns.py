import re

def keyword(pattern, **kwargs):
    """Return regular expresssion pattern that matches a keyword prefix.

    :param prefix: Keyword prefix character (default: ``\"+\"``).
    :param pattern: Prefix string (or pattern)
    :param name: The group name for the remaining text (default: ``\"text\"``).
    :param split: Boolean value whether to split message on prefix character (default: ``True``).

    Examples::

      keyword('reg')
      keyword('register|reg')
      keyword('reg', prefix=\"(+|@)\")

    """

    name = kwargs.pop("name", "text")
    prefix = kwargs.pop("prefix", "+")
    split = kwargs.pop("split", True)

    if split:
        remaining = '^%s' % re.escape(prefix)
    else:
        remaining = '.'

    return '^%s\s*(%s)(\s+(?P<%s>[%s]*)|$)' % (
        re.escape(prefix), pattern, name, remaining)
