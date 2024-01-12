# Generated by Django 3.2 on 2023-07-27 11:38

from django.db import migrations
import django_resized.forms
import mcl.models


class Migration(migrations.Migration):

    dependencies = [
        ('mcl', '0050_remove_entrylist_current_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklist',
            name='topic_image',
            field=django_resized.forms.ResizedImageField(blank=True, crop=None, force_format=None, keep_meta=True, null=True, quality=-1, scale=None, size=[1024, 768], upload_to=mcl.models.CheckList.image_dir),
        ),
    ]
