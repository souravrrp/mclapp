# Generated by Django 3.2 on 2022-06-29 13:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mcl', '0018_auto_20220629_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklist',
            name='entry_list',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mcl.entrylist'),
        ),
        migrations.AlterField(
            model_name='entrylist',
            name='otp',
            field=models.CharField(max_length=10, null=True, unique=True),
        ),
    ]
