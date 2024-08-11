from django.contrib.contenttypes.models import ContentType


def get_content_type(model):
    """Return the ContentType object for a given model, creating the ContentType if necessary.
    Lookups are cached so that subsequent lookups for the same model don't hit the database."""
    return ContentType.objects.get_for_model(model)
