import bleach
from bleach.linkifier import LinkifyFilter
from urllib.parse import urlparse
from functools import partial

_allowed_tags=tags=['a',
                    'b',
                    'blockquote',
                    'code',
                    'em',
                    'h1',
                    'h2',
                    'h3',
                    'h4',
                    'h5',
                    'h6',
                    'i',
                    'li',
                    'ol',
                    'p',
                    'strong',
                    'ul',
                   ]

_allowed_tags_with_links=_allowed_tags+["a"]

_allowed_attributes={'a': ['href', 'title']}

_allowed_protocols=['http', 'https']

#filter to make all links show domain on hover
def nofollow(attrs, new=False):
    attrs["rel"]="nofollow"
    return attrs

_callback_functions=bleach.linkifier.DEFAULT_CALLBACKS+[nofollow]

_clean_wo_links = bleach.Cleaner(tags=_allowed_tags,
                                  attributes=_allowed_attributes,
                                  protocols=_allowed_protocols,
                                  )
_clean_w_links = bleach.Cleaner(tags=_allowed_tags,
                                  attributes=_allowed_attributes,
                                  protocols=_allowed_protocols,
                                  filters=[partial(LinkifyFilter,
                                                   skip_tags=["pre"],
                                                   parse_email=False,
                                                   callbacks=_callback_functions
                                                   )
                                          ]
                                  )


def sanitize(text, linkgen=False):

    if linkgen:
        return _clean_w_links.clean(text)
    else:
        return _clean_wo_links.clean(text)
    

