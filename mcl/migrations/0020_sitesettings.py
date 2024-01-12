# Generated by Django 3.2 on 2022-06-30 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mcl', '0019_auto_20220629_1329'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_id', models.CharField(choices=[('main', 'main')], default='main', editable=False, max_length=50)),
                ('name', models.CharField(blank=True, default='App Name', max_length=100, null=True)),
                ('title', models.CharField(blank=True, default='App Title', max_length=100, null=True)),
                ('description', models.TextField(blank=True, default='Description', null=True)),
            ],
        ),
    ]
