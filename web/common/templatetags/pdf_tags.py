from django import template
from django.template.loader import get_template, render_to_string
from django.template.base import Node, token_kwargs
from typing import Union
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def pdf_embed(id="pdf", src=None, **kwargs) -> bool:
    """Generates a container for an embedded PDF iFrame.

    Parameters
    ==========
    id : str, default="pdf"
        The id of the pdf that will be created
    src : str, optional
        URL to the PDF to be embedded
    import_static : bool, default=False
        Import the static files required if not imported in page header

    Examples
    --------
    ::

        {% pdf_embed id="app_pdf" src="app:get_pdf" %}
        {% pdf_embed id="app_pdf" src="https://domain.com/file.pdf" %}
    """
    try:
        src = reverse(src, kwargs=kwargs)
    except NoReverseMatch:
        pass

    return render_to_string('common/pdf/container.html', {'id': id, 'src': src})


@register.simple_tag
def pdf_import_static():
    """Imports the necessary static files for embedded pdfs to work."""
    stylesheets = [
        "/static/common/pdf/css/pdf_embed.css",
        "https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.9.1/viewer.min.css",
    ]
    scripts = [
        # "/static/common/pdf/js/pdf_embed.js",
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.10.377/pdf.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/viewerjs/1.9.1/viewer.min.js",
        # "https://cdnjs.cloudflare.com/ajax/libs/pdfobject/2.2.14/pdfobject.min.js",  # Not needed?
    ]

    imports = ''

    for stylesheet in stylesheets:
        imports += f'<link rel="stylesheet" type="text/css" href="{stylesheet}">'

    for script in scripts:
        imports += f'<script type="application/javascript" src="{script}"></script>'

    return mark_safe(imports)
