# Generated by Django 3.1.7 on 2021-09-06 09:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0032_auto_20210906_0917'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='donation',
            name='pdf_file',
        ),
    ]