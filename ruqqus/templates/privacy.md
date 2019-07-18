{% extends "default.html" %}

{% block content %}
{% filter Markdown %}
# Privacy

Ruqqus uses encrypted cookies to maintain secure authenticated sessions. These cookies are randomized with each new session.

You can see the information associated with your account [here](/my_info).

{% endfilter %}
{% endblock
