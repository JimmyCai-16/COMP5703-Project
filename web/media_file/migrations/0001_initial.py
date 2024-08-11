# Generated by Django 4.1.5 on 2023-10-11 00:52

from django.db import migrations, models
import django.db.models.deletion
import media_file.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MediaFile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=256)),
                ('content_type', models.CharField(editable=False, max_length=256)),
                ('file', models.FileField(max_length=500, upload_to=media_file.models.instanced_file_path)),
                ('file_size', models.PositiveIntegerField(editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('tag', models.PositiveIntegerField(choices=[(0, 'Dataset'), (1, 'Document'), (2, 'Report'), (3, 'Form'), (4, 'Cleaner'), (5, 'Application'), (6, 'Compliance'), (7, 'Receipt'), (8, 'Model'), (9, 'Task')], null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MediaFileRelationship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='media_file.mediafile')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='media_file.mediafile')),
            ],
        ),
        migrations.AddField(
            model_name='mediafile',
            name='children',
            field=models.ManyToManyField(related_name='parents', through='media_file.MediaFileRelationship', to='media_file.mediafile'),
        ),
        migrations.AddConstraint(
            model_name='mediafilerelationship',
            constraint=models.UniqueConstraint(fields=('parent', 'child'), name='media_file_mediafilerelationship_unique_relationships'),
        ),
        migrations.AddConstraint(
            model_name='mediafilerelationship',
            constraint=models.CheckConstraint(check=models.Q(('parent', models.F('child')), _negated=True), name='media_file_mediafilerelationship_prevent_self_add'),
        ),
    ]
