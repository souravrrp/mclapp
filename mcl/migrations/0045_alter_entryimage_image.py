# Generated by Django 3.2 on 2022-09-05 11:36

from django.db import migrations, models
import mcl.models


class Migration(migrations.Migration):

    dependencies = [
        ('mcl', '0044_alter_entryimage_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entryimage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=mcl.models.EntryImage.file_dir),
        ),
    ]