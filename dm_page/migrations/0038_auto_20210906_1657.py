# Generated by Django 3.1.7 on 2021-09-06 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm_page', '0037_remove_donation_pdf_receipt'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnnualReceiptTrigger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='donationreceipt',
            name='canceled',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='donationreceipt',
            name='date_created',
            field=models.DateField(auto_now_add=True, null=True),
        ),
    ]