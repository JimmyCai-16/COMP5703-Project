"""
``Object Permission`` template tags. To use in a template just put the following
*load* tag inside a template::

    {% load permission_tags %}

"""
from django import template
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.utils.encoding import force_str

from object_permissions.core import P

register = template.Library()


def get_cache_name(user):
    """Gets the name of the context var where the users permission cache is stored."""
    return '__%s_permission_handler' % force_str(user.pk)


class ObjectPermissionsNode(template.Node):

    def __init__(self, user, obj, context_var):
        self.user = template.Variable(user)
        self.obj = template.Variable(obj)
        self.context_var = context_var.strip("'\"")

    def render(self, context):

        user = self.user.resolve(context)

        if not isinstance(user, get_user_model()):
            raise ValueError("Invalid argument value for User")

        cache = P.from_user(user)

        obj = self.obj.resolve(context)
        context[self.context_var] = cache.get_perm(obj)

        return ''


@register.tag
def get_perms(parser, token):
    """Retrieves and stores a list of permissions the supplied ``user`` has for the ``object`` within the named context
    variable. Super Users always return a full list of permissions for a given object.
    Will utilize existing cached permissions, or will create a new cache.

    Example::

        {% get_obj_perms user inventory as "inventory_perms" %}

        {% if "delete_item" in inventory_perms %}
            <a href="/inventory/delete?item={{ item.id }}">Delete {{ item.name }}</a>
        {% endif %}
    """
    try:
        _, user, obj, _, context_var = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('get_perms tag should be in format "{% get_perms user obj as "context_var" %}"')

    # Ensure that the context_var is encapsulated in quotes
    if context_var[0] != context_var[-1] or context_var[0] not in ('"', "'"):
        raise template.TemplateSyntaxError(f"get_perms ``context_var`` should be in matching single or double quotes.")

    return ObjectPermissionsNode(user, obj, context_var)


class HasPermNode(template.Node):
    def __init__(self, permission, user, obj, nodelist_true, nodelist_false):
        self.permission = permission.strip("'\"")
        self.user = template.Variable(user)
        self.obj = template.Variable(obj)
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context, **kwargs):
        user = self.user.resolve(context)
        obj = self.obj.resolve(context)

        if user is None or not user.is_authenticated or obj is None:
            return self.nodelist_false.render(context)

        cache = P.from_user(user)

        if cache.has_perm(self.permission, obj, False):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)


@register.tag
def has_perm(parser, token):
    """Checks if a ``user`` has ``permission`` for a supplied ``obj`` (always true for super-users).
    Will utilize existing cached permissions, or will create a new cache.

    Example::

        {% has_perm "delete_items" user inventory %}
            You're allowed to delete items!
        {% else %}
            You're not allowed to delete items!
        {% endhas_perm %}
    """
    try:
        tag_name, permission, user, obj = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('has_perm should be in format "{% has_perm "permission" user obj %}"')

    # Ensure that the permission name is encapsulated in quotes
    if permission[0] != permission[-1] or permission[0] not in ('"', "'"):
        raise template.TemplateSyntaxError(f"has_perm ``permission`` should be in matching single or double quotes.")

    # Get the nodelist for the 'else' block if present
    nodelist_true = parser.parse(('else', 'endhas_perm'))

    # Check if the 'else' block exists
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endhas_perm',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()

    return HasPermNode(permission, user, obj, nodelist_true, nodelist_false)


