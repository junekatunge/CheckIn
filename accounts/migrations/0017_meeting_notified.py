# Generated by Django 4.2.16 on 2024-10-15 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_remove_meeting_checked_out'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='notified',
            field=models.BooleanField(default=False),
        ),
    ]