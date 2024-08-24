# Generated by Django 4.1.5 on 2023-10-11 00:52

import adminsortable.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('project_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='assignees',
            field=models.ManyToManyField(related_name='tasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='column',
            field=adminsortable.fields.SortableForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='project_management.column'),
        ),
        migrations.AddField(
            model_name='task',
            name='labels',
            field=models.ManyToManyField(related_name='tasks', to='project_management.label'),
        ),
        migrations.AddField(
            model_name='task',
            name='user_created',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_owned_tasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='user_updated',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='updated_tasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='label',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='project_management.board'),
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='project_management.task'),
        ),
        migrations.AddField(
            model_name='column',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='columns', to='project_management.board'),
        ),
        migrations.AddField(
            model_name='board',
            name='members',
            field=models.ManyToManyField(related_name='boards', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='board',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='owned_boards', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='board',
            name='user_created',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_owned_task_list_boards', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='board',
            name='user_updated',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='updated_task_list_boards', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='label',
            constraint=models.UniqueConstraint(fields=('name', 'board'), name='unique_name_board'),
        ),
    ]