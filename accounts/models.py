from django.db import models
import datetime
from django.utils import timezone
from django.core.mail import send_mail 
from background_task import background
import threading



# Create your models here.

# HOST MODEL
class Host(models.Model):
    # id = models.AutoField
    host_name = models.CharField(max_length=50)
    host_email = models.EmailField(blank=True, null=True)
    host_phone = models.CharField(max_length=15)
    host_image = models.ImageField(upload_to='img/doctors',default='img/doctors/profile_default.png')
    host_desc = models.CharField(max_length=50)
    address = models.CharField(max_length=100,default="CheckMate, Rohini-22, New Delhi")
    status = models.BooleanField(default=True)
    available = models.CharField(max_length=50,default='')
    # current_meeting_id = models.IntegerField(blank=True, null=True)
    current_meeting = models.ForeignKey('Meeting', on_delete=models.SET_NULL, null=True, blank=True,related_name='current_host')


    # def __str__(self):
    #     return str(self.id) + " : " + str(self.host_name)
    def __str__(self):
        return f"{self.host_name}"

# MEETING MODEL

from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings  # ✅ Use your configured email

class Meeting(models.Model):
    VISITOR_TYPE_CHOICES = [
        ('GENERAL', 'General'),
        ('VIP', 'VIP'),
        ('BUSINESS', 'Business'),
    ]

    national_no = models.BigIntegerField(unique=False)
    visitor_name = models.CharField(max_length=50)
    visitor_email = models.EmailField(blank=True, null=True)
    visitor_phone = models.CharField(max_length=15)
    visitor_type = models.CharField(max_length=10, choices=VISITOR_TYPE_CHOICES, default='GENERAL')
    host = models.ForeignKey('Host', on_delete=models.CASCADE, related_name='meetings')
    date = models.DateField(default=timezone.now)
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(blank=True, null=True)
    queue_number = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('waiting', 'Waiting'), ('completed', 'Completed')], default='waiting')
    notified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.assign_queue_number()

    def assign_queue_number(self):
        waiting = Meeting.objects.filter(
            host=self.host, time_out__isnull=True
        ).order_by('time_in')

        for idx, meeting in enumerate(waiting, start=1):
            meeting.queue_number = idx
            meeting.notified = False  # Reset to force new notification
            meeting.save(update_fields=['queue_number', 'notified'])

        self.notify_queue_positions(waiting)

    def notify_queue_positions(self, waiting):
        for meeting in waiting:
            print(f"DEBUG: Processing {meeting.visitor_name} Pos: {meeting.queue_number} Notified: {meeting.notified} Email: {meeting.visitor_email}")

            if not meeting.visitor_email:
                print(f"DEBUG: Skipping {meeting.visitor_name} — No email.")
                continue

            if meeting.queue_number == 1 and not meeting.notified:
                subject = "You're Next In Line"
                message = (
                    f"Hello {meeting.visitor_name},\n\n"
                    f"You are now next in line to see {meeting.host.host_name}."
                )
            elif not meeting.notified:
                subject = "Your Queue Position"
                message = (
                    f"Hello {meeting.visitor_name},\n\n"
                    f"Your current position to see {meeting.host.host_name} is {meeting.queue_number}."
                )
            else:
                print(f"DEBUG: Skipping {meeting.visitor_name} — Already notified.")
                continue

            try:
                print(f"🚀 Sending: {subject} to {meeting.visitor_email}")
                send_mail(subject, message, settings.EMAIL_HOST_USER, [meeting.visitor_email])
                meeting.notified = True
                meeting.save(update_fields=['notified'])
                print(f"✅ Notified {meeting.visitor_name} — Position {meeting.queue_number}")
            except Exception as e:
                print(f"❌ Failed to notify {meeting.visitor_name}: {e}")

    def checkout(self):
        self.time_out = timezone.now()
        self.status = 'completed'
        self.save(update_fields=['time_out', 'status'])

        self.host.current_meeting = None
        self.host.status = True
        self.host.save(update_fields=['current_meeting', 'status'])

        waiting = Meeting.objects.filter(
            host=self.host, time_out__isnull=True
        ).order_by('time_in')

        for idx, meeting in enumerate(waiting, start=1):
            meeting.queue_number = idx
            meeting.notified = False
            meeting.save(update_fields=['queue_number', 'notified'])

        self.notify_queue_positions(waiting)

    def __str__(self):
        return f"{self.visitor_name} - {self.host.host_name} (Position: {self.queue_number})"
