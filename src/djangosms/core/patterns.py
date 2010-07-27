import re
import settings

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
    prefix = kwargs.pop("prefix", settings.KEYWORD_PREFIX)
    split = kwargs.pop("split", True)

    if prefix:
        prefix_re = re.escape(prefix)
    else:
        prefix_re = ''

    if split and prefix:
        remaining_re = '[^%s]' % prefix_re
    else:
        remaining_re = '.'

    regex = '^%s\s*(%s)(\s+(?P<%s>%s*)|$)' % (prefix_re, pattern, name, remaining_re)

    return regex
