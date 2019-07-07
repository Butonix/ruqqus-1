from bleach import linkify
from bleach.linkifier import LinkifyFilter

_allowed_tags=tags=['b',
                   'blockquote',
                   'code',
                   'em',
                   'i',
                   'li',
                   'ol',
                   'strong',
                   'ul'
                   ]

_allowed_tags_with_links=_allowed_tags+["a"]

_allowed_attributes={'a': ['href', 'title']}

_allowed_protocols=['http', 'https']

def _url_on_hover(attrs, new=False):
    attrs["title"]=attrs["href"]
    return attrs

_callback_functions=bleach.linkifier.DEFAULT_CALLBACKS+[_url_on_hover]

_clean_wo_links = bleach.Cleaner(tags=_allowed_tags,
                                  attributes=_allowed_attributes,
                                  protocols=_allowed_protocols,
                                  callbacks=_callback_functions
                                  )
_clean_w_links = bleach.Cleaner(tags=_allowed_tags,
                                  attributes=_allowed_attributes,
                                  protocols=_allowed_protocols,
                                  callbacks=_callback_functions,
                                  filters=[lambda:LinkifyFilter(skip_tags=["pre"],
                                                                parse_email=False)
                                      ]
                                  )


def sanitize(text, linkgen=False):

    if linkgen:
        return _clean_w_links.clean(text)
    else:
        return _clean_wo_links.clean(text)
    

