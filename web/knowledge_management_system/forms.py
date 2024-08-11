from django import forms

from forms.forms import CategoryChoiceWidget
from knowledge_management_system.models import *
from project.models import Project, ProjectMember


class InlineRadioSelect(forms.RadioSelect):
    template_name = 'knowledge_management_system/forms/widgets/inline_check.html'
    option_template_name = 'knowledge_management_system/forms/widgets/inline_check_option.html'


class AbstractKMSReportForm(forms.ModelForm):
    template_name = ''
    project = None
    prospect = None
    form_templates = forms.ModelChoiceField(queryset=None, label='Templates', required=False)

    instance_id = forms.CharField(widget=forms.HiddenInput(attrs={'class' : 'instance_id_val'}), required=False)

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        self.kms_project = self.project.kms

        super().__init__(*args, **kwargs)
        # form-control form-control-sm
        self.fields['prospect_tags'].widget = forms.SelectMultiple(attrs={'class': 'selectpicker form-control w-100'})
        self.fields['prospect_tags'].queryset = KMSProspect.objects.filter(prospect__project=self.project)

        self.fields['form_templates'].widget = forms.Select(attrs={'class': 'form-select w-auto'})
        self.fields['form_templates'].queryset = self.Meta.model.objects.filter(kms_project=self.kms_project, is_template=True)

    def clean(self):
        cleaned_data = super().clean()
        prospect_tags = cleaned_data.get('prospect_tags')

        if prospect_tags:
            pass

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.kms_project = self.kms_project

        if commit:
            instance.save()
            self.save_m2m()

        return instance

    class Meta:
        abstract = True
        model = AbstractKMSReport
        exclude = ('kms_project', 'editable',)


class KMSWorkReportForm(AbstractKMSReportForm):
    template_name = 'knowledge_management_system/forms/work_report_form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['distribution'].required = False
        self.fields['summary'].required = False

    class Meta(AbstractKMSReportForm.Meta):
        model = KMSWorkReport
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of_work': forms.Select(attrs={'class': 'form-select'}),
            'distribution': forms.Textarea(attrs={'data-tinymce-f': ''}),
            'summary': forms.Textarea(attrs={'data-tinymce-f': ''}),
        }


class KMSStatusReportForm(AbstractKMSReportForm):
    template_name = 'knowledge_management_system/forms/status_report_form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['health_safety_status'].required = False
        self.fields['enviro_status'].required = False
        self.fields['community_status'].required = False
        self.fields['operational_summary'].required = False
        self.fields['personnel_at_site'].required = False
        self.fields['distribution'].required = False

    class Meta(AbstractKMSReportForm.Meta):
        model = KMSStatusReport
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'manager': forms.TextInput(attrs={'class': 'form-control'}),
            'distribution': forms.Textarea(attrs={'data-tinymce-f': '', 'id': "id_distribution_status"}),
            **{
                key: forms.Textarea(attrs={'data-tinymce-f': ''})
                for key in ['health_safety_status', 'enviro_status', 'community_status', 'operational_summary', 'personnel_at_site']
            },
            **{
                key: InlineRadioSelect(choices=((0, 'No'), (1, 'Yes')), attrs={'class': 'form-check form-check-inline'})
                for key in ['was_reportable_hns_incident', 'was_reportable_enviro_incident', 'was_community_interaction', 'is_noted_in_lms']
            }
        }


class KMSHistoricalReportForm(AbstractKMSReportForm):
    template_name = 'knowledge_management_system/forms/historical_report_form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['summary'].required = False
    class Meta(AbstractKMSReportForm.Meta):
        model = KMSHistoricalReport
        widgets = {
            'report_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'tenure_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_published': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'type_of_work': forms.Select(attrs={'class': 'form-select'}),
            'distribution': forms.Textarea(attrs={'data-tinymce-f': ''}),
            'summary': forms.Textarea(attrs={'data-tinymce-f': '', 'id':"id_summary_historical"}),
        }
