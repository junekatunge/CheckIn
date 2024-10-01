from django.db import models
import datetime
from django.utils import timezone

# Create your models here.

# HOST MODEL
class Host(models.Model):
    # id = models.AutoField
    host_name = models.CharField(max_length=50)
    host_email = models.EmailField(blank=True, null=True)
    host_phone = models.CharField(max_length=15)
    host_image = models.ImageField(upload_to='img/doctors')
    host_desc = models.CharField(max_length=50)
    address = models.CharField(max_length=100,default="HealthPlus, Rohini-22, New Delhi")
    status = models.BooleanField(default=True)
    # available = models.CharField(max_length=50,default='')
    # current_meeting_id = models.IntegerField(blank=True, null=True)
    # current_meeting = models.ForeignKey('Meeting', on_delete=models.SET_NULL, null=True, blank=True)


    # def __str__(self):
    #     return str(self.id) + " : " + str(self.host_name)
    def __str__(self):
        return f"{self.host_name}"

# MEETING MODEL
class Meeting(models.Model):
    VISITOR_TYPE_CHOICES = [
        ('GENERAL', 'General'),
        ('VIP', 'VIP'),
        ('BUSINESS', 'Business'),
    ]

    visitor_name = models.CharField(max_length=50)
    visitor_email = models.EmailField(blank=True, null=True)
    visitor_phone = models.CharField(max_length=15)  # Changed to CharField for phone numbers
    visitor_type = models.CharField(max_length=10, choices=VISITOR_TYPE_CHOICES, default='GENERAL')
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='meetings')  # Added related_name to access all meetings related to a host
    date = models.DateField(default=timezone.now)  # Use timezone.now for dynamic current date
    time_in = models.TimeField(default=timezone.now)  # Use timezone.now for dynamic current time
    time_out = models.TimeField(blank=True, null=True)

    def send_notification_email(self):
        subject = f"Visitor {self.visitor_name} has checked in"
        message = f"Visitor Name: {self.visitor_name}\nVisitor Type: {self.visitor_type}\nCheck-in Time: {self.time_in.strftime('%H:%M:%S')}\nMeeting Date: {self.date.strftime('%Y-%m-%d')}"
        recipient_list = [self.host.host_email]
        if self.visitor_email:
            recipient_list.append(self.visitor_email)
        
        send_mail(
            subject,
            message,
            'your_email@gmail.com',  # Change to your Gmail
            recipient_list,
            fail_silently=False,
        )

    def __str__(self):
        return f"{self.visitor_name} - {self.host.host_name}"

    # def __str__(self):
    #     return str(self.id)+ ' : ' + str(self.visitor_name)

