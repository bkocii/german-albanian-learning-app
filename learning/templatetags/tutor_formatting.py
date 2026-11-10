import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_BOLD_MARKDOWN = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.DOTALL)


@register.filter
def tutor_rich_text(value):
    """Render only Markdown-style bold after escaping all tutor text."""
    escaped = escape(str(value or ""))
    rendered = _BOLD_MARKDOWN.sub(r"<strong>\1</strong>", escaped)
    return mark_safe(rendered)
