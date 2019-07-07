import bleach
from bleach.linkify import LinkifyFilter

_allowed_tags=tags=['a',
                   'b',
                   'blockquote',
                   'code',
                   'em',
                   'i',
                   'li',
                   'ol',
                   'strong',
                   'ul'
                   ]

_allowed_attributes={'a': ['href', 'title'],
                    styles=[]}

_allowed_protocols=['http', 'https']

CleanWithoutLinkgen = lambda x:bleach.Cleaner(tags=_allowed_tags,
                                     attributes=_allowed_attributes,
                                     protocols=_allowed_protocols
                                     ).clean(x)

def _url_on_hover(attrs, new=False):
    attrs["title"]=attrs["href"]
    return attrs

_callback_functions=bleach.linkifier.DEFAULT_CALLBACKS+[_url_on_hover]


CleanWithLinkgen = lambda x:bleach.Cleaner(tags=_allowed_tags,
                                  attributes=_allowed_attributes,
                                  protocols=_allowed_protocols,
                                  callbacks=_callback_functions
                                  filters=[lambda:LinkifyFilter(skip_tags=["pre"],
                                                                parse_email=False)
                                      ]
                                  ).clean(x)
