from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required
from .models import Host, Meeting
from .forms import Meeting_form, Add_profile
import datetime
import requests
import json
import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.

@login_required(login_url='/admin_login/')
def dashboard(request):
    # Fetch all hosts and order them by name for display
    hosts = Host.objects.all().order_by('host_name')
    # Fetch meetings related to the hosts
    meetings = Meeting.objects.all()

    # Prepare the context with hosts and meetings
    context = {
        'hosts': hosts,
        'meetings': meetings,
    }

    return render(request, 'dashboard.html', {'hosts': hosts})

@login_required(login_url='/admin_login/')
def verify(request):
    if request.method == 'POST':
        key = request.POST.get('password')
        user = auth.authenticate(username=request.user.username, password=key)
        if user is not None:
            # If verifying profile, render profile manager
            if request.POST.get('profile'):
                form = Add_profile()
                return render(request, 'profile_manager.html', {'form': form})

            # If logging out, redirect to home
            if request.POST.get('logout'):
                auth.logout(request)
                return redirect('/')

            # If checking meeting history, fetch today's meetings
            if request.POST.get('meeting'):
                today = timezone.now().date()  # Get today's date
                meetings = Meeting.objects.filter(date=today)  # Use __date lookup to compare only the date part
                return render(request, 'meeting_history.html', {'meetings': reversed(list(meetings))})
        else:
            # If credentials are invalid, show a warning
            messages.warning(request, 'Please enter valid credentials!')
            return redirect('/dashboard')
    else:
        return redirect('/dashboard')
from django.shortcuts import render, redirect, get_object_or_404
@login_required(login_url='/admin_login/')
def meeting_manager(request):
    if request.method == 'POST':
        # If visitor button is clicked, visitor details are shown
        if request.POST.get("visitor"): 
            meeting_id = request.POST.get("visitor")

            print(f"Visitor Button Clicked. Meeting ID: {meeting_id}")  # Debugging
            
            try:
                meeting = Meeting.objects.get(id=meeting_id)
                host = Host.objects.get(current_meeting=meeting)  # Using current_meeting ForeignKey

                print(f"Meeting Retrieved: {meeting.visitor_name}, Host: {host.host_name}")
                
            except Meeting.DoesNotExist:
                messages.error(request, 'Meeting not found.')
                return redirect('/dashboard')
            except Host.DoesNotExist:
                messages.error(request, 'Host not found.')
                return redirect('/dashboard')

            # Render visitor details template
            meeting_details = {'meeting': meeting, 'host': host}

            # Debugging: Check what data is passed to the template
            print(f"Meeting Details Passed to Template: {meeting_details}")
            
            return render(request, 'visitor_details.html', meeting_details)

        # If meeting button is clicked, open the meeting form
        elif request.POST.get("meeting"): 
            host_id = request.POST.get("meeting")

            try:
                host = Host.objects.get(id=host_id)
            except Host.DoesNotExist:
                messages.error(request, 'Host not found.')
                return redirect('/dashboard')

            form = Meeting_form()
            param = {'form': form, 'host': host}
            return render(request, 'meeting_form.html', param)

        else:
            messages.error(request, 'Invalid request.')
            return redirect('/dashboard')
    
    else:
        meetings = Meeting.objects.all()
        hosts = Host.objects.all()
        return render(request, 'meeting_list.html', {'meetings': meetings, 'hosts': hosts})

from django.core.mail import send_mail

def send_meeting_email(subject, instance, recipient_list):
    # Prepare the email message
    message = f"Visitor {instance.visitor_name} has checked in at {instance.time_in.strftime('%H:%M:%S')} on {instance.date.strftime('%Y-%m-%d')}."
    
    # Send the email
    send_mail(
        subject,
        message,
        'jkatunge13@gmail.com',  # Replace with your Gmail address or the email you configured for sending
        recipient_list,
        fail_silently=False,
    )

def send_checkout_email(meeting):
    # Prepare the email subject and message
    subject = f"Visitor {meeting.visitor_name} Checked Out"
    message = f"Visitor {meeting.visitor_name} checked out at {meeting.time_out.strftime('%H:%M:%S')} on {meeting.date.strftime('%Y-%m-%d')}."
    recipient_list = [meeting.visitor_email] if meeting.visitor_email else []
    
    # Call the general email function
    send_email(subject, message, recipient_list)


# Saves the visitor details filled in meeting form
# Saves the visitor details filled in meeting form
@login_required(login_url='/admin_login/')
def save_meeting(request):
    if request.method == 'POST':
        # Retrieve the host name from the form
        host_name = request.POST.get('host')
        
        # Fetch the host instance using the host name
        try:
            host = Host.objects.get(host_name=host_name)
        except Host.DoesNotExist:
            messages.error(request, 'Host does not exist.')
            return redirect('/dashboard')

        # Create an instance of MeetingForm with POST data
        form = Meeting_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)  # Don't save to the database yet

            # Set current time and assign the host instance
            instance.time_in = datetime.datetime.now()
            instance.host = host  # Assign the Host object, not the name
            
            # Save the meeting instance to the database
            instance.save()
            
            # Update the host's current meeting
            host.current_meeting_id = instance.id
            host.status = False
            host.save()

            # Prepare email and SMS notifications
            rec = [host.host_email]
            subject = instance.visitor_name + " Checked In!"
            visitor = instance

            # Send email and SMS notifications
            email(subject, visitor, rec)
            # sendsms(subject, visitor, host)

            messages.success(request, 'Information sent to Host, You will be called shortly!')
            return redirect('/dashboard')
        else:
            messages.error(request, 'There was an error with the form. Please correct it.')
            return redirect('/dashboard')
    else:
        return redirect('/dashboard')


# # Saves the visitor details filled in meeting form
# @login_required(login_url='/admin_login/')
# def save_meeting(request):
#     if request.method == 'POST':
#         # Retrieve the host name from the form
#         host_name = request.POST.get('host')
        
#         # Fetch the host instance using the host name
#         try:
#             host = Host.objects.get(host_name=host_name)
#         except Host.DoesNotExist:
#             messages.error(request, 'Host does not exist.')
#             return redirect('/dashboard')

#         # Create an instance of MeetingForm with POST data
#         form = Meeting_form(request.POST)
#         if form.is_valid():
#             instance = form.save(commit=False)  # Don't save to the database yet
            
#             # Assign the host instance to the meeting
#             instance.host = host  # Set the host instance
#             instance.time_in = timezone.now()  # Set current time
#             instance.save()  # Now save the instance to the database
            
#             # Update the host's current meeting
#             host.current_meeting = instance  # Update the current meeting
#             host.status = False  # Set status to not available
#             host.save()  # Save the host instance
            
#             # Send email notifications
#             rec = [host.host_email]
#             subject = f"{instance.visitor_name} Checked In!"
#             email(subject, instance, rec, host)

#             messages.success(request, 'Information sent to Host, You will be called shortly!')
#             return redirect('/dashboard')
#         else:
#             messages.error(request, 'There was an error with the form. Please correct it.')
#     else:
#         return redirect('/dashboard')


# Checkout function when Host clicks checkout button
@login_required(login_url='/admin_login/')
def checkout(request):
    if request.method == 'GET':  # Change to accept GET requests
        meeting_id = request.GET.get('mid')  # Get meeting ID from the URL query parameter

        # Fetch the meeting using the ID
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        # Check if the visitor has already checked out
        if meeting.time_out:
            return HttpResponse(f"{meeting.visitor_name}, already checked out!")
        
        # Set the checkout time
        meeting.time_out = timezone.now()  # Capture the current time as checkout time
        meeting.save()  # Save the updated meeting instance
        
        # Update the host's status and current meeting
        host = meeting.host  # Get the associated host
        host.current_meeting = None  # Clear the current meeting
        host.status = True  # Set the host's status to available
        host.save()  # Save the updated host instance

        # Optionally, send a checkout notification email (if desired)
        send_checkout_email(meeting)
        
        return HttpResponse(f"{meeting.visitor_name}, checked out successfully!")
    
    return HttpResponse("Invalid request method.")  # Handle invalid methods


def send_checkout_email(meeting):
    # Prepare the checkout notification email
    subject = f"Visitor {meeting.visitor_name} Checked Out"
    message = (
        f"Dear {meeting.visitor_name},\n"
        f"You have successfully checked out at {meeting.time_out.strftime('%H:%M:%S')} on {meeting.date.strftime('%Y-%m-%d')}."
    )
    recipient_list = [meeting.visitor_email] if meeting.visitor_email else []
    
    # Send the email (ensure you have configured your email settings)
    send_mail(subject, message, 'jkatunge13@gmail.com', recipient_list, fail_silently=False)

# Sends the email to both host and visitor
def email(subject,visitor,rec,host=None):
    ## FILL IN YOUR DETAILS HERE
    sender = 'jkatunge13@gmail.com'
    if host:
        html_content = render_to_string('visitor_mail_template.html', {'visitor':visitor,'host':host}) # render with dynamic value
    else:
        html_content = render_to_string('host_mail_template.html', {'visitor':visitor}) # render with dynamic value
    
    text_content = strip_tags(html_content)

    # try except block to avoid wesite crashing due to email error
    try:
        msg = EmailMultiAlternatives(subject, text_content, sender, rec)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"Email successfully sent to: {rec}")
    except Exception as e:
        logging.error(f"Error sending email to {rec}: {e}")
        print(f"Failed to send email: {e}")  # To log and see the error during development


# profile manager that saves host profile
@login_required(login_url='/admin_login/')
def profile_manager(request):
    # Manage host profiles: add or edit
    if request.method == 'POST':
        form = Add_profile(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Save the new host profile
            return redirect('/dashboard')
    return redirect('/dashboard')

@login_required(login_url='/admin_login/')
def edit_profile(request):
    # Edit an existing host profile
    if request.method == 'POST':
        host_id = request.POST.get('editing')
        instance = Host.objects.filter(id=host_id).first()
        form = Add_profile(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()  # Save the updated host profile
            return redirect('/dashboard')
    return redirect('/dashboard')

@login_required(login_url='/admin_login/')
def edit_delete(request):
    # Edit or delete host profiles based on user action
    if request.method == 'POST':
        host_id = request.POST.get('id')
        host = Host.objects.filter(id=host_id).first()
        if host:
            # If editing, show the profile manager form
            if request.POST.get('edit'):
                form = Add_profile(instance=host)
                return render(request, 'profile_manager.html', {'form': form, 'edit': True, 'info': host_id})
            # If deleting, remove the host profile
            elif request.POST.get('delete'):
                host.delete()
                return redirect('/dashboard')
        else:
            messages.warning(request, 'Profile not found!')
            return redirect('/dashboard')
    return redirect('/dashboard')

# def send_checkout_email(meeting):
#     # Send a checkout notification email to the visitor
#     subject = f"Visitor {meeting.visitor_name} Checked Out"
#     message = f"Visitor {meeting.visitor_name} checked out at {meeting.time_out.strftime('%H:%M:%S')} on {meeting.date.strftime('%Y-%m-%d')}"
#     recipient_list = [meeting.visitor_email] if meeting.visitor_email else []
#     send_mail(subject, message, 'jkatunge13@gmail.com', recipient_list, fail_silently=False)
