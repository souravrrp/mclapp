# Generated by Django 3.2 on 2022-06-29 09:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_currentuser.db.models.fields
import django_currentuser.middleware


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mcl', '0012_auto_20220628_1242'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(max_length=250, null=True)),
                ('status', models.BooleanField(default=True, null=True)),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
            },
        ),
        migrations.RenameField(
            model_name='entrylist',
            old_name='option',
            new_name='otp',
        ),
        migrations.RemoveField(
            model_name='entrylist',
            name='point',
        ),
        migrations.AddField(
            model_name='entrylist',
            name='comment',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='entrylist',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='entrylist',
            name='created_by',
            field=django_currentuser.db.models.fields.CurrentUserField(default=django_currentuser.middleware.get_current_authenticated_user, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entrylist',
            name='updated_by',
            field=django_currentuser.db.models.fields.CurrentUserField(default=django_currentuser.middleware.get_current_authenticated_user, null=True, on_delete=django.db.models.deletion.CASCADE, on_update=True, related_name='updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entrylist',
            name='comment_one',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='comment_one', to='mcl.comment'),
        ),
        migrations.AddField(
            model_name='entrylist',
            name='comment_three',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='comment_three', to='mcl.comment'),
        ),
        migrations.AddField(
            model_name='entrylist',
            name='comment_two',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='comment_two', to='mcl.comment'),
        ),
    ]
