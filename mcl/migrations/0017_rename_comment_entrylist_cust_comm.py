# Generated by Django 3.2 on 2022-06-29 10:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mcl', '0016_auto_20220629_0941'),
    ]

    operations = [
        migrations.RenameField(
            model_name='entrylist',
            old_name='comment',
            new_name='cust_comm',
        ),
    ]
