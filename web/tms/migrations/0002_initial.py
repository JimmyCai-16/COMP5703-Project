# Generated by Django 4.1.5 on 2023-10-11 00:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('project', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tms', '0001_initial'),
        ('media_file', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenementtask',
            name='authority',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='my_tasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tenementtask',
            name='files',
            field=models.ManyToManyField(blank=True, null=True, related_name='task_file', to='media_file.mediafile'),
        ),
        migrations.AddField(
            model_name='tenementtask',
            name='tenement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='tms.tenement'),
        ),
        migrations.AddField(
            model_name='tenementholder',
            name='tenement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holders', to='tms.tenement'),
        ),
        migrations.AddField(
            model_name='tenement',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tenements', to='project.project'),
        ),
        migrations.AddField(
            model_name='target',
            name='created_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='target',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='targets', to='project.project'),
        ),
        migrations.AddField(
            model_name='qldtenementblock',
            name='tenement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='tms.tenement'),
        ),
        migrations.AddField(
            model_name='qldenvironmentalauthority',
            name='tenement',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='environmental_authority', to='tms.tenement'),
        ),
        migrations.AddField(
            model_name='moratorium',
            name='tenement',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tms.tenement'),
        ),
        migrations.AlterUniqueTogether(
            name='workprogram',
            unique_together={('tenement', 'year', 'discipline', 'activity')},
        ),
        migrations.AddIndex(
            model_name='tenement',
            index=models.Index(fields=['permit_type', 'permit_status'], name='tms_tenemen_permit__2cb9ec_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='tenement',
            unique_together={('permit_state', 'permit_type', 'permit_number')},
        ),
        migrations.AlterUniqueTogether(
            name='target',
            unique_together={('project', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='qldtenementblock',
            unique_together={('tenement', 'block_identification_map', 'number', 'status')},
        ),
    ]
