# Generated by Django 3.2 on 2023-08-07 11:55

from django.db import migrations, models
import mcl.models


class Migration(migrations.Migration):

    dependencies = [
        ('mcl', '0053_alter_topic_sample_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='sample_image',
            field=models.ImageField(blank=True, null=True, upload_to=mcl.models.Topic.sample_image),
        ),
    ]
