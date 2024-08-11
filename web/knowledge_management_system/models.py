from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.postgres import fields as postgres

from project.models import Project
from tms.models import Target

# TODO: TextFields below with comments next to them to be looked 
# into at a later date, due to unconstrained nature of TextFields

# https://abr.business.gov.au/Help/EntityTypeList
ENTITY_TYPES = [
    (1, 'Approved Deposit Fund',),
    (107, 'APRA Regulated Non-Public Offer Fund',),
    (108, 'APRA Regulated Public Offer Fund',),
    (2, 'APRA Regulated Fund (Fund Type Unknown)',),
    (24, 'ATO Regulated Self-Managed Superannuation Fund',),
    (19, 'Australian Private Company',),
    (23, 'Australian Public Company',),
    (66, 'Cash Management Trust',),
    (67, 'Commonwealth Government APRA Regulated Public Sector Fund',),
    (68, 'Commonwealth Government APRA Regulated Public Sector Scheme',),
    (70, 'Commonwealth Government Cash Management Trust',),
    (52, 'Commonwealth Government Company',),
    (57, 'Commonwealth Government Co-operative',),
    (65, 'Commonwealth Government Corporate Unit Trust',),
    (74, 'Commonwealth Government Discretionary Investment Trust',),
    (71, 'Commonwealth Government Discretionary Services Management Trust',),
    (77, 'Commonwealth Government Discretionary Trading Trust',),
    (53, 'Commonwealth Government Entity',),
    (72, 'Commonwealth Government Fixed Trust',),
    (78, 'Commonwealth Government Fixed Unit Trust',),
    (73, 'Commonwealth Government Hybrid Trust',),
    (58, 'Commonwealth Government Limited Partnership',),
    (75, 'Commonwealth Government Listed Public Unit Trust',),
    (69, 'Commonwealth Government Non-Regulated Super Fund',),
    (60, 'Commonwealth Government Other Incorporated Entity',),
    (59, 'Commonwealth Government Other Unincorporated Entity',),
    (54, 'Commonwealth Government Partnership',),
    (61, 'Commonwealth Government Pooled Development Fund',),
    (62, 'Commonwealth Government Private Company',),
    (56, 'Commonwealth Government Public Company',),
    (64, 'Commonwealth Government Public Trading Trust',),
    (51, 'Commonwealth Government Statutory Authority',),
    (63, 'Commonwealth Government Strata Title',),
    (55, 'Commonwealth Government Super Fund',),
    (32, 'Commonwealth Government Trust',),
    (76, 'Commonwealth Government Unlisted Public Unit Trust',),
    (3, 'Co-operative',),
    (156, 'Corporate Collective Investment Vehicle (CCIV) Sub-Fund',),
    (4, 'Corporate Unit Trust',),
    (5, 'Deceased Estate',),
    (6, 'Diplomatic/Consulate Body or High Commission',),
    (79, 'Discretionary Investment Trust',),
    (80, 'Discretionary Services Management Trust',),
    (81, 'Discretionary Trading Trust',),
    (9, 'Family Partnership',),
    (155, 'First Home Saver Accounts (FHSA) Trust',),
    (83, 'Fixed Trust',),
    (82, 'Fixed Unit Trust',),
    (84, 'Hybrid Trust',),
    (12, 'Individual/Sole Trader',),
    (15, 'Limited Partnership',),
    (110, 'Listed Public Unit Trust',),
    (95, 'Local Government APRA Regulated Public Sector Fund',),
    (96, 'Local Government APRA Regulated Public Sector Scheme',),
    (98, 'Local Government Cash Management Trust',),
    (34, 'Local Government Company',),
    (86, 'Local Government Co-operative',),
    (94, 'Local Government Corporate Unit Trust',),
    (102, 'Local Government Discretionary Investment Trust',),
    (99, 'Local Government Discretionary Services Management Trust',),
    (105, 'Local Government Discretionary Trading Trust',),
    (35, 'Local Government Entity',),
    (100, 'Local Government Fixed Trust',),
    (106, 'Local Government Fixed Unit Trust',),
    (101, 'Local Government Hybrid Trust',),
    (87, 'Local Government Limited Partnership',),
    (103, 'Local Government Listed Public Unit Trust',),
    (97, 'Local Government Non-Regulated Super Fund',),
    (89, 'Local Government Other Incorporated Entity',),
    (88, 'Local Government Other Unincorporated Entity',),
    (36, 'Local Government Partnership',),
    (90, 'Local Government Pooled Development Fund',),
    (91, 'Local Government Private Company',),
    (85, 'Local Government Public Company',),
    (93, 'Local Government Public Trading Trust',),
    (33, 'Local Government Statutory Authority',),
    (92, 'Local Government Strata Title',),
    (38, 'Local Government Trust',),
    (104, 'Local Government Unlisted Public Unit Trust',),
    (16, 'Non-Regulated Superannuation Fund',),
    (17, 'Other Incorporated Entity',),
    (21, 'Other Partnership',),
    (30, 'Other Trust',),
    (31, 'Other Unincorporated Entity',),
    (18, 'Pooled Development Fund',),
    (20, 'Pooled Superannuation Trust',),
    (22, 'Public Trading Trust',),
    (111, 'Small APRA Fund',),
    (122, 'State Government APRA Regulated Public Sector Scheme',),
    (124, 'State Government Cash Management Trust',),
    (40, 'State Government Company',),
    (113, 'State Government Co-operative',),
    (121, 'State Government Corporate Unit Trust',),
    (128, 'State Government Discretionary Investment Trust',),
    (125, 'State Government Discretionary Services Management Trust',),
    (131, 'State Government Discretionary Trading Trust',),
    (41, 'State Government Entity',),
    (126, 'State Government Fixed Trust',),
    (132, 'State Government Fixed Unit Trust',),
    (127, 'State Government Hybrid Trust',),
    (114, 'State Government Limited Partnership',),
    (129, 'State Government Listed Public Unit Trust',),
    (123, 'State Government Non-Regulated Super Fund',),
    (116, 'State Government Other Incorporated Entity',),
    (115, 'State Government Other Unincorporated Entity',),
    (42, 'State Government Partnership',),
    (117, 'State Government Pooled Development Fund',),
    (118, 'State Government Private Company',),
    (112, 'State Government Public Company',),
    (120, 'State Government Public Trading Trust',),
    (39, 'State Government Statutory Authority',),
    (119, 'State Government Strata Title',),
    (44, 'State Government Trust',),
    (130, 'State Government Unlisted Public Unit Trust',),
    (25, 'State Government APRA Regulated Public Sector Fund',),
    (27, 'Strata-title',),
    (28, 'Super fund',),
    (143, 'Territory Government APRA Regulated Public Sector Fund',),
    (144, 'Territory Government APRA Regulated Public Sector Scheme',),
    (146, 'Territory Government Cash Management Trust',),
    (134, 'Territory Government Co-operative',),
    (142, 'Territory Government Corporate Unit Trust',),
    (150, 'Territory Government Discretionary Investment Trust',),
    (147, 'Territory Government Discretionary Services Management Trust',),
    (153, 'Territory Government Discretionary Trading Trust',),
    (47, 'Territory Government Entity',),
    (148, 'Territory Government Fixed Trust',),
    (154, 'Territory Government Fixed Unit Trust',),
    (149, 'Territory Government Hybrid Trust',),
    (135, 'Territory Government Limited Partnership',),
    (151, 'Territory Government Listed Public Unit Trust',),
    (145, 'Territory Government Non-Regulated Super Fund',),
    (137, 'Territory Government Other Incorporated Entity',),
    (136, 'Territory Government Other Unincorporated Entity',),
    (48, 'Territory Government Partnership',),
    (138, 'Territory Government Pooled Development Fund',),
    (139, 'Territory Government Private Company',),
    (133, 'Territory Government Public Company',),
    (141, 'Territory Government Public Trading Trust',),
    (45, 'Territory Government Statutory Authority',),
    (140, 'Territory Government Strata Title',),
    (50, 'Territory Government Trust',),
    (152, 'Territory Government Unlisted Public Unit Trust',),
    (109, 'Unlisted Public Unit Trust'),
]

WORK_TYPE_CHOICES = [
    (0, 'Geology'),
    (1, 'Geochemistry'),
    (2, 'Geophysics'),
    (3, 'Structural Geology'),
]

class Company(models.Model):
    acn = models.CharField(max_length=9, verbose_name='Australian Company Number', blank=True, null=True)
    abn = models.CharField(max_length=11, verbose_name='Australian Business Number', blank=True, null=True)

    abn_status = models.CharField(max_length=20, null=True, blank=True)
    abn_status_date = models.DateField(null=True, blank=True)

    entity_type = models.PositiveSmallIntegerField(choices=ENTITY_TYPES, blank=True, null=True)

    name = models.CharField(max_length=256)
    address = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['acn'],
                condition=Q(acn__isnull=False),
                name='unique_acn_not_null'
            ),
            models.UniqueConstraint(
                fields=['abn'],
                condition=Q(abn__isnull=False),
                name='unique_abn_not_null'
            ),
        ]

    def get_entity_type_description_url(self):
        return f"https://abr.business.gov.au/Help/EntityTypeDescription?Id={self.entity_type}"


class KMSProject(models.Model):

    model_name = 'project'

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='kms', editable=False)

    # TextFields below to be looked into at a later date, due to unconstrained length
    outline = models.TextField() #CharField(max_length=4096, blank=True, null=True)
    previous_exploration_synopsis = models.TextField() #CharField(max_length=4096, blank=True, null=True)

    class Meta:
        default_permissions = ('change',)
        permissions = [
            ('modify_prospect', 'Modify Prospect'),
            ('report_add', 'Add Report'),
            ('report_modify', 'Modify Report'),
            ('report_delete', 'Remove Report'),
            ('update_permissions', 'Update Permissions'),
        ]


class KMSProspect(models.Model):

    model_name = 'prospect'

    prospect = models.OneToOneField(Target, on_delete=models.CASCADE, related_name='kms')
    is_template = models.BooleanField(default=False)

    rationale = models.TextField() #CharField(max_length=4096, blank=True, null=True)
    hypothesis = models.TextField() #CharField(max_length=4096, blank=True, null=True)
    objectives = models.TextField() #CharField(max_length=4096, blank=True, null=True)
    previous_exploration_synopsis = models.TextField() #CharField(max_length=4096, blank=True, null=True)

    def __str__(self):
        return self.prospect.name

    def get_name(self):
        return self.prospect.name

    def as_instance_dict(self):

        coordinates = self.prospect.location.split(" ")
        location = "[ " + coordinates[0] + ", " + coordinates[1] + " ]"

        return {
            'id': self.id,
            'name': self.prospect.name,
            'prospect_id':self.prospect.id,
            'rationale': self.rationale,
            'hypothesis': self.hypothesis,
            'objectives': self.objectives,
            'location': location,
            'description': self.prospect.description,
            'previous_exploration_synopsis': self.previous_exploration_synopsis,
        }


# class KMSProspectTag(models.Model):
#     prospect = models.ForeignKey(KMSProspect, on_delete=models.CASCADE, related_name='tags')
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     content_object = GenericForeignKey('content_type', 'object_id')


class AbstractKMSReport(models.Model):

    model_name = 'abstract_report'

    kms_project = models.ForeignKey(KMSProject, on_delete=models.CASCADE)
    is_template = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    name = models.CharField(max_length=128)
    author = models.CharField(max_length=64)

    prospect_tags = models.ManyToManyField(KMSProspect)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def as_instance_dict(self):
        """Used for returning the instance as a JSON response for the frontend."""
        return {}


class KMSWorkReport(AbstractKMSReport):

    model_name = 'work_report'

    type_of_work = models.PositiveSmallIntegerField(choices=WORK_TYPE_CHOICES, default=0)
    distribution = models.TextField()
    summary = models.TextField()

    def as_instance_dict(self):
        return {
            'id': self.id,
            'project': self.kms_project.project.name,
            'date_created': self.date_created.strftime("%m/%d/%Y"),
            'name': self.name,
            'author': self.author,
            'prospect_tags': [{'value': tag.pk, 'label': tag.get_name()} for tag in self.prospect_tags.all()],
            'type_of_work': {'value': self.type_of_work, 'label': self.get_type_of_work_display()},
            'distribution': self.distribution,
            'summary': self.summary,
        }


class KMSStatusReport(AbstractKMSReport):

    model_name = 'status_report'

    YES_NO_CHOICES = [
        (0, 'No'),
        (1, 'Yes')
    ]

    manager = models.CharField(max_length=64)

    distribution = models.TextField() #CharField(max_length=64)

    personnel_at_site = postgres.ArrayField(models.CharField(max_length=64))

    was_reportable_hns_incident = models.IntegerField(choices=YES_NO_CHOICES, default=0)
    health_safety_status = models.TextField() #CharField(max_length=4096, null=True, blank=True)

    was_reportable_enviro_incident = models.IntegerField(choices=YES_NO_CHOICES, default=0)
    enviro_status = models.TextField() #CharField(max_length=4096, null=True, blank=True)

    was_community_interaction = models.IntegerField(choices=YES_NO_CHOICES, default=0)
    is_noted_in_lms = models.IntegerField(choices=YES_NO_CHOICES, default=0)
    community_status = models.TextField() #CharField(max_length=4096, null=True, blank=True)

    operational_summary = models.TextField() #CharField(max_length=4096)

    def _validate_radio_textarea_constraint(self, radio_name, text_area_name):
        """Checks that a textarea set to yes, has content in its associated textarea"""

        if getattr(self, radio_name) == 1 and not getattr(self, text_area_name):
            radio_name_display = radio_name.replace('_', ' ').title()
            text_area_name_display = text_area_name.replace('_', ' ').title()

            raise ValidationError({text_area_name: f"{text_area_name_display} is required when {radio_name_display} is set."})

    def clean(self):
        self._validate_radio_textarea_constraint('was_reportable_hns_incident', 'health_safety_status')
        self._validate_radio_textarea_constraint('was_reportable_enviro_incident', 'enviro_status')
        self._validate_radio_textarea_constraint('was_community_interaction', 'community_status')

    def as_instance_dict(self):
        return {
            'id': self.id,
            'project': self.kms_project.project.name,
            'date_created': self.date_created.strftime("%m/%d/%Y"),
            'name': self.name,
            'author': self.author,
            'manager': self.manager,
            'prospect_tags': [{'value': tag.pk, 'label': tag.get_name()} for tag in self.prospect_tags.all()],
            'distribution': self.distribution,

            'personnel_at_site': self.personnel_at_site,

            'was_reportable_hns_incident': self.was_reportable_hns_incident,
            'health_safety_status': self.health_safety_status,

            'was_reportable_enviro_incident': self.was_reportable_enviro_incident,
            'enviro_status': self.enviro_status,

            'was_community_interaction': self.was_community_interaction,
            'is_noted_in_lms': self.is_noted_in_lms,
            'community_status': self.community_status,
            'operational_summary': self.operational_summary,
        }


class KMSHistoricalReport(AbstractKMSReport):

    model_name = 'historical_report'

    type_of_work = models.PositiveSmallIntegerField(choices=WORK_TYPE_CHOICES, default=0)
    report_id = models.CharField(max_length=64)
    company = models.CharField(max_length=64)
    tenure_number = models.CharField(max_length=64)
    date_published = models.DateField()
    summary = models.TextField() #CharField(max_length=4096)

    def as_instance_dict(self):
        return {
            'id': self.id,
            'project': self.kms_project.project.name,
            'name': self.name,
            'author': self.author,
            'prospect_tags': [{'value': tag.pk, 'label': tag.get_name()} for tag in self.prospect_tags.all()],
            'type_of_work': {'value': self.type_of_work, 'label': self.get_type_of_work_display()},
            'report_id': self.report_id,
            'company': self.company,
            'tenure_number': self.tenure_number,
            'date_published': self.date_published.strftime("%m/%d/%Y"),
            'summary': self.summary,
        }
