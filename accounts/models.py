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
    host_image = models.ImageField(upload_to='img/doctors')
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
    date = models.DateField(default=timezone.now)  # # Automatically set on creation
    time_in = models.DateTimeField(auto_now_add=True)  # Use timezone.now for dynamic current time
    time_out = models.DateTimeField(blank=True, null=True)  # Allow null for checkout time
    
    # New fields
    queue_number = models.IntegerField(null=True, blank=True)  # Queue position
    status = models.CharField(max_length=10, choices=[('waiting', 'Waiting'), ('completed', 'Completed')], default='waiting')


    def schedule_queue_notification(self):
        # Notify the visitor after 5 minutes
        timer = threading.Timer(300, self.send_queue_notification)  # 300 seconds = 5 minutes
        timer.start()
        
    def send_queue_notification(self):
        # Logic to send notification (e.g., email or SMS) to the visitor
        subject = "Your Queue Position"
        message = f"Hello {self.visitor_name}, you are currently in position {self.get_queue_position()}."
        send_mail(subject, message, 'from@example.com', [self.visitor_email])  # Adjust the from address
     
    def get_queue_position(self):
        # Logic to determine the visitor's position in the queue
        # For example, you might count how many meetings are scheduled before this one
        return Meeting.objects.filter(time_in__lt=self.time_in).count() + 1
    
    def __str__(self):
        return f"{self.visitor_name} - {self.host.host_name}"

    # def __str__(self):
    #     return str(self.id)+ ' : ' + str(self.visitor_name)

