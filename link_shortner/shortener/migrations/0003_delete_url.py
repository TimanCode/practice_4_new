# Generated by Django 4.2.6 on 2023-11-10 12:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0002_alter_url_short_url'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Url',
        ),
    ]
