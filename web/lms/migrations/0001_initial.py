# Generated by Django 4.1.5 on 2024-08-26 14:39

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import lms.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('media_file', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandParcelOwnerCorrespondence',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=32)),
                ('content', models.CharField(max_length=512)),
            ],
            options={
                'ordering': ['owner', '-date_updated'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LandParcelOwnerNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=32)),
                ('content', models.CharField(max_length=512)),
            ],
            options={
                'ordering': ['owner', '-date_updated'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LandParcelOwnerReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=32)),
                ('content', models.CharField(max_length=512)),
                ('date_due', models.DateField()),
            ],
            options={
                'ordering': ['owner', '-date_updated'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LandParcelOwnerTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=32)),
                ('content', models.CharField(max_length=512)),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'Not Started'), (1, 'In Progress'), (2, 'Review'), (3, 'Completed'), (4, 'On hold')], default=0)),
                ('priority', models.PositiveSmallIntegerField(choices=[(0, 'None'), (1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Very High'), (5, 'Immediate')], default=2)),
                ('date_due', models.DateField()),
            ],
            options={
                'ordering': ['-status', '-priority', 'owner', '-date_updated'],
            },
        ),
        migrations.CreateModel(
            name='LMSHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('object_id', models.CharField(blank=True, max_length=36, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('modified_json', models.JSONField()),
                ('json', models.JSONField()),
            ],
            options={
                'ordering': ['-date_created'],
            },
        ),
        migrations.CreateModel(
            name='Parcel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('lot', models.CharField(blank=True, max_length=5, null=True)),
                ('plan', models.CharField(blank=True, max_length=10, null=True)),
                ('tenure', models.CharField(blank=True, max_length=40, null=True)),
                ('lot_area', models.FloatField(blank=True, null=True, verbose_name='Area')),
                ('exl_lot_area', models.FloatField(blank=True, null=True, verbose_name='Excluded Area')),
                ('lot_volume', models.FloatField(blank=True, null=True, verbose_name='Lot Volume')),
                ('feature_name', models.CharField(blank=True, max_length=60, null=True, verbose_name='Name')),
                ('alias_name', models.CharField(blank=True, max_length=400, null=True, verbose_name='Alias Name')),
                ('accuracy_code', models.CharField(blank=True, max_length=40, null=True, verbose_name='Accuracy')),
                ('surv_index', models.CharField(blank=True, max_length=1, null=True, verbose_name='Surveyed')),
                ('cover_type', models.CharField(blank=True, max_length=10, null=True, verbose_name='Coverage Type')),
                ('parcel_type', models.CharField(blank=True, max_length=24, null=True, verbose_name='Parcel Type')),
                ('locality', models.CharField(blank=True, max_length=30, null=True, verbose_name='Locality')),
                ('shire_name', models.CharField(blank=True, max_length=40, null=True, verbose_name='Local Government Area')),
                ('smis_map', models.CharField(blank=True, max_length=100, null=True)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(editable=False, srid=4326)),
                ('geometry_hash', models.BinaryField(db_index=True, default=lms.models.default_geometry_hash, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='ParcelOwner',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('title', models.PositiveSmallIntegerField(choices=[(0, 'N/A'), (1, 'Mr'), (2, 'Ms'), (3, 'Mrs'), (4, 'Miss'), (5, 'Other')], default=0)),
                ('first_name', models.CharField(max_length=32)),
                ('last_name', models.CharField(max_length=32)),
                ('preferred_name', models.CharField(blank=True, max_length=128, null=True)),
                ('gender', models.PositiveSmallIntegerField(choices=[(0, 'N/A'), (1, 'Male'), (2, 'Female'), (3, 'Other'), (4, 'Undisclosed')], default=0)),
                ('date_birth', models.DateField(blank=True, null=True)),
                ('address_street', models.CharField(blank=True, max_length=512, null=True)),
                ('address_postal', models.CharField(blank=True, max_length=512, null=True)),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('contact_phone', models.CharField(blank=True, max_length=32, null=True)),
                ('contact_mobile', models.CharField(blank=True, max_length=32, null=True)),
                ('contact_fax', models.CharField(blank=True, max_length=32, null=True)),
            ],
            options={
                'ordering': ['-date_updated'],
            },
        ),
        migrations.CreateModel(
            name='ParcelOwnerRelationship',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_mail_target', models.BooleanField(default=False)),
                ('date_ownership_start', models.DateField(blank=True, null=True)),
                ('date_ownership_ceased', models.DateField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProjectParcel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('files', models.ManyToManyField(blank=True, related_name='land_parcel_files', to='media_file.mediafile')),
                ('owners', models.ManyToManyField(blank=True, related_name='parcels', through='lms.ParcelOwnerRelationship', to='lms.parcelowner')),
                ('parcel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lms.parcel')),
            ],
            options={
                'ordering': ['-date_updated'],
            },
        ),
    ]
