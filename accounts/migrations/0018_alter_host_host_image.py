# Generated by Django 4.2.16 on 2024-10-16 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_meeting_notified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='host_image',
            field=models.ImageField(default='img/doctors/profile_default.png', upload_to='img/doctors'),
        ),
    ]