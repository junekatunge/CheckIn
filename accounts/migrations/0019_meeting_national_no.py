# Generated by Django 4.2.16 on 2024-10-24 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_alter_host_host_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='national_no',
            field=models.IntegerField(default=1234567, max_length=20),
            preserve_default=False,
        ),
    ]
