# Generated by Django 3.2 on 2022-05-30 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mcl', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'verbose_name': 'Topic', 'verbose_name_plural': 'Topics'},
        ),
        migrations.RemoveField(
            model_name='category',
            name='name',
        ),
        migrations.RemoveField(
            model_name='topic',
            name='name',
        ),
        migrations.AddField(
            model_name='category',
            name='name_bn',
            field=models.CharField(max_length=500, null=True, verbose_name='Bangla Name'),
        ),
        migrations.AddField(
            model_name='category',
            name='name_en',
            field=models.CharField(max_length=500, null=True, verbose_name='English Name'),
        ),
        migrations.AddField(
            model_name='topic',
            name='name_bn',
            field=models.CharField(max_length=500, null=True, verbose_name='Bangla Name'),
        ),
        migrations.AddField(
            model_name='topic',
            name='name_en',
            field=models.CharField(max_length=500, null=True, verbose_name='English Name'),
        ),
    ]
