# Generated by Django 3.1.7 on 2021-10-19 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0085_auto_20211019_0559'),
    ]

    operations = [
        migrations.DeleteModel(
            name='StorePayload',
        ),
        migrations.AddField(
            model_name='webhooklogs',
            name='processed',
            field=models.BooleanField(default=False),
        ),
    ]