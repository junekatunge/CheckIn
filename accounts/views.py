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
from django.utils import timezone

# Create your views here.

@login_required(login_url='/admin_login/')
def dashboard(request):
    # Fetch all hosts and order them by name for display
    hosts = Host.objects.all().order_by('host_name')
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

@login_required(login_url='/admin_login/')
def meeting_manager(request):
    if request.method == 'POST':
        # If visitor button is clicked, visitor details are shown
        if request.POST.get("visitor"): 
            meeting_id = request.POST.get("visitor")
            
            try:
                meeting = Meeting.objects.get(id=meeting_id)
                host = Host.objects.get(current_meeting_id=meeting_id)

                
            except Meeting.DoesNotExist:
                messages.error(request, 'Meeting not found.')
                return redirect('/dashboard')
            except Host.DoesNotExist:
                messages.error(request, 'Host not found.')
                return redirect('/dashboard')

            # Render visitor details template
            meeting_details = {'meeting': meeting, 'host': host}
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

        # Fallback for POST request with no valid action
        else:
            messages.error(request, 'Invalid request.')
            return redirect('/dashboard')

    else:
        # Handle GET requests
        meetings = Meeting.objects.all()
        hosts = Host.objects.all()
        return render(request, 'meeting_list.html', {'meetings': meetings, 'hosts': hosts})

    # if not request.user.is_authenticated:
    #     return redirect('login')  # Redirect to login if user is not authenticated

    # # Retrieve meetings and hosts as needed
    # meetings = Meeting.objects.all()  # You might want to filter this based on user
    # hosts = Host.objects.all()  # Again, consider filtering based on user or roles

    # # Render the template with the context
    # return render(request, 'meeting_form.html', {'meetings': meetings, 'hosts': hosts})

def email(subject, visitor, rec, host=None):
    # Function to send emails based on the visitor and host details
    sender = 'your_email@gmail.com'  # Replace with your email
    if host:
        html_content = render_to_string('visitor_mail_template.html', {'visitor': visitor, 'host': host})
    else:
        html_content = render_to_string('host_mail_template.html', {'visitor': visitor})

    text_content = strip_tags(html_content)

    try:
        msg = EmailMultiAlternatives(subject, text_content, sender, rec)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        print(f"Error sending email: {e}")

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
            
            # Assign the host instance to the meeting
            instance.host = host  # Set the host instance
            instance.time_in = timezone.now()  # Set current time
            instance.save()  # Now save the instance to the database
            
            # Update the host's current meeting
            host.current_meeting = instance  # Update the current meeting
            host.status = False  # Set status to not available
            host.save()  # Save the host instance
            
            # Send email notifications
            rec = [host.host_email]
            subject = f"{instance.visitor_name} Checked In!"
            email(subject, instance, rec, host)

            messages.success(request, 'Information sent to Host, You will be called shortly!')
            return redirect('/dashboard')
        else:
            messages.error(request, 'There was an error with the form. Please correct it.')
    else:
        return redirect('/dashboard')


@login_required(login_url='/admin_login/')
@login_required(login_url='/admin_login/')
def checkout(request):
    # Handle visitor checkout process
    if request.method == 'GET':
        meeting_id = request.GET['mid']
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            return HttpResponse("Meeting not found!")
        
        # Check if the visitor has already checked out
        if meeting.time_out:
            return HttpResponse(f"{meeting.visitor_name}, Already Checked Out!")
        
        meeting.time_out = timezone.now()  # Set checkout time
        meeting.save()  # Save updated meeting

        # Update the host's status and current meeting
        host = meeting.host  # Get the associated host
        host.current_meeting = None  # Clear the current meeting
        host.status = True  # Set host status to available
        host.save()  # Save the updated host

        send_checkout_email(meeting)  # Send checkout email notification
        return HttpResponse(f"{meeting.visitor_name}, Checked Out Successfully!")


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

def send_checkout_email(meeting):
    # Send a checkout notification email to the visitor
    subject = f"Visitor {meeting.visitor_name} Checked Out"
    message = f"Visitor {meeting.visitor_name} checked out at {meeting.time_out.strftime('%H:%M:%S')} on {meeting.date.strftime('%Y-%m-%d')}"
    recipient_list = [meeting.visitor_email] if meeting.visitor_email else []
    send_mail(subject, message, 'your_email@gmail.com', recipient_list, fail_silently=False)
