# Generated by Django 3.2 on 2022-06-29 09:39

from django.conf import settings
from django.db import migrations
import django.db.models.deletion
import django_currentuser.db.models.fields
import django_currentuser.middleware


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mcl', '0014_alter_entrylist_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entrylist',
            name='created_by',
            field=django_currentuser.db.models.fields.CurrentUserField(default=django_currentuser.middleware.get_current_authenticated_user, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='entrylist',
            name='updated_by',
            field=django_currentuser.db.models.fields.CurrentUserField(default=django_currentuser.middleware.get_current_authenticated_user, null=True, on_delete=django.db.models.deletion.CASCADE, on_update=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
