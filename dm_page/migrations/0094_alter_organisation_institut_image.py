# Generated by Django 3.2.3 on 2021-10-27 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0093_alter_organisation_institut_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisation',
            name='institut_image',
            field=models.FileField(blank=True, null=True, upload_to='', verbose_name="Image de l'Institut"),
        ),
    ]
