from django import forms
from object_permissions.core import assign_perm, get_user_perms_list, get_model_perms, remove_perm


class ObjectPermissionsForm(forms.Form):
    template_name = 'object_permissions/forms/permission_form.html'

    def __init__(self, user, obj, *args, **kwargs):
        self.user = user
        self.obj = obj

        ## DEBUG TEST PERMISSION CREATION STUFF ##
        import object_permissions.core as op
        from object_permissions.models import ObjectPermission

        ObjectPermission.objects.filter(user=user).delete()

        op.assign_perm("report_add", user, obj)
        op.assign_perm("report_modify", user, obj)
        op.assign_perm("report_delete", user, obj)
        ## END DEBUG TEST DATA ##

        super().__init__(*args, **kwargs)

        self.fields['permission'] = forms.MultipleChoiceField(
            label='Permissions',
            choices=self.get_obj_permission_choices(),
            initial=self.get_obj_permission_initial(),
            widget=forms.SelectMultiple,
            required=False
        )

        print('CURRENT DATA', self.fields['permission'].initial)

    def get_obj_permission_choices(self):
        """Returns the model permissions as a list of choices"""
        return [(p.codename, p.name) for p in get_model_perms(self.obj)]

    def get_obj_permission_initial(self):
        """Returns the model permissions as a list of choices"""
        return get_user_perms_list(self.user, self.obj)
