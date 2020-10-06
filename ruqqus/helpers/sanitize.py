import bleach
from bs4 import BeautifulSoup
from bleach.linkifier import LinkifyFilter
from urllib.parse import urlparse, ParseResult, urlunparse
from functools import partial
from .get import *

_allowed_tags = tags = ['b',
                        'blockquote',
                        'br',
                        'code',
                        'del',
                        'em',
                        'h1',
                        'h2',
                        'h3',
                        'h4',
                        'h5',
                        'h6',
                        'hr',
                        'i',
                        'li',
                        'ol',
                        'p',
                        'pre',
                        'strong',
                        'sub',
                        'sup',
                        'table',
                        'tbody',
                        'th',
                        'thead',
                        'td',
                        'tr',
                        'ul'
                        ]

_allowed_tags_with_links = _allowed_tags + ["a",
                                            "img"
                                            ]

_allowed_tags_in_bio = [
    'a',
    'b',
    'blockquote',
    'code',
    'del',
    'em',
    'i',
    'p',
    'pre',
    'strong',
    'sub',
    'sup'
]

_allowed_attributes = {'a': ['href', 'title', "rel"],
                       'img': ['src', 'class']
                       }

_allowed_protocols = ['http', 'https']

# filter to make all links show domain on hover


def nofollow(attrs, new=False):

    parsed_url = urlparse(attrs[(None, "href")])
    domain = parsed_url.netloc
    if domain and not domain.endswith(("ruqqus.com", "ruqq.us")):
        attrs[(None, "rel")] = "nofollow noopener"
        attrs[(None, "target")] = "_blank"

        # Force https for all external links in comments
        # (Ruqqus already forces its own https)
        new_url = ParseResult(scheme="https",
                              netloc=parsed_url.netloc,
                              path=parsed_url.path,
                              params=parsed_url.params,
                              query=parsed_url.query,
                              fragment=parsed_url.fragment)

        attrs[(None, "href")] = urlunparse(new_url)

    return attrs


_clean_wo_links = bleach.Cleaner(tags=_allowed_tags,
                                 attributes=_allowed_attributes,
                                 protocols=_allowed_protocols,
                                 )
_clean_w_links = bleach.Cleaner(tags=_allowed_tags_with_links,
                                attributes=_allowed_attributes,
                                protocols=_allowed_protocols,
                                filters=[partial(LinkifyFilter,
                                                 skip_tags=["pre"],
                                                 parse_email=False,
                                                 callbacks=[nofollow]
                                                 )
                                         ]
                                )

_clean_bio = bleach.Cleaner(tags=_allowed_tags_in_bio,
                            attributes=_allowed_attributes,
                            protocols=_allowed_protocols,
                            filters=[partial(LinkifyFilter,
                                             skip_tags=["pre"],
                                             parse_email=False,
                                             callbacks=[nofollow]
                                             )
                                     ]
                            )


def sanitize(text, bio=False, linkgen=False):

    text = text.replace("\ufeff", "")

    if linkgen:
        if bio:
            sanitized = _clean_bio.clean(text)
        else:
            sanitized = _clean_w_links.clean(text)

        soup = BeautifulSoup(sanitized, features="html.parser")

        for tag in soup.find_all("img"):

            url = tag.get("src", "")
            if not url:
                continue
            netloc = urlparse(url).netloc

            domain = get_domain(netloc)
            if not(netloc) or (domain and domain.show_thumbnail):

                if "profile-pic-20" not in tag.get("class", ""):
                    # set classes and wrap in link

                    tag["rel"] = "nofollow"
                    tag["style"] = "max-height: 100px; max-width: 100%;"
                    tag["class"] = "in-comment-image rounded-sm my-2"

                    link = soup.new_tag("a")
                    link["href"] = tag["src"]
                    link["rel"] = "nofollow noopener"
                    link["target"] = "_blank"

                    link["onclick"] = f"expandDesktopImage('{tag['src']}');"
                    link["data-toggle"] = "modal"
                    link["data-target"] = "#expandImageModal"

                    tag.wrap(link)
            else:
                # non-whitelisted images get replaced with links
                new_tag = soup.new_tag("a")
                new_tag.string = tag["src"]
                new_tag["href"] = tag["src"]
                new_tag["rel"] = "nofollow noopener"
                tag.replace_with(new_tag)

        sanitized = str(soup)

    else:
        sanitized = _clean_wo_links.clean(text)

    return sanitized
