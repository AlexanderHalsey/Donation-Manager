# Generated by Django 3.1.7 on 2021-08-22 09:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0024_auto_20210821_0929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='details',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='phone',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='postal_address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='donation',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dm_page.contact'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='date_donated',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='donation',
            name='donation_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dm_page.donationtype'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='organisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dm_page.organisation'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='payment_mode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dm_page.paymentmode'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='pdf_path',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]