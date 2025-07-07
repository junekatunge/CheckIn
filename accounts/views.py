from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import auth
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Host, Meeting
from .forms import Meeting_form, Add_profile
import pytz
import logging

# -------------------------------------------
# DASHBOARD
# -------------------------------------------
@login_required(login_url='/admin_login/')
def dashboard(request):
    hosts = Host.objects.all().order_by('host_name')
    meetings = Meeting.objects.all()
    return render(request, 'dashboard.html', {'hosts': hosts, 'meetings': meetings})

# -------------------------------------------
# VERIFY FUNCTION
# -------------------------------------------
@login_required(login_url='/admin_login/')
def verify(request):
    if request.method == 'POST':
        key = request.POST.get('password')
        user = auth.authenticate(username=request.user.username, password=key)
        if user:
            if request.POST.get('profile'):
                form = Add_profile()
                return render(request, 'profile_manager.html', {'form': form})
            if request.POST.get('logout'):
                auth.logout(request)
                return redirect('/')
            if request.POST.get('meeting'):
                today = timezone.now().date()
                meetings = Meeting.objects.filter(date=today)
                return render(request, 'meeting_history.html', {'meetings': reversed(list(meetings))})
        else:
            messages.warning(request, 'Please enter valid credentials!')
            return redirect('/dashboard')
    return redirect('/dashboard')

# -------------------------------------------
# MEETING MANAGER
# -------------------------------------------
@login_required(login_url='/admin_login/')
def meeting_manager(request):
    if request.method == 'POST':
        if request.POST.get("visitor"):
            meeting_id = request.POST.get("visitor")
            try:
                meeting = Meeting.objects.get(id=meeting_id)
                host = Host.objects.get(current_meeting=meeting)
            except Meeting.DoesNotExist:
                messages.error(request, 'Meeting not found.')
                return redirect('/dashboard')
            except Host.DoesNotExist:
                messages.error(request, 'Host not found.')
                return redirect('/dashboard')
            return render(request, 'visitor_details.html', {'meeting': meeting, 'host': host})
        elif request.POST.get("meeting"):
            host_id = request.POST.get("meeting")
            try:
                host = Host.objects.get(id=host_id)
            except Host.DoesNotExist:
                messages.error(request, 'Host not found.')
                return redirect('/dashboard')
            form = Meeting_form()
            return render(request, 'meeting_form.html', {'form': form, 'host': host})
        else:
            messages.error(request, 'Invalid request.')
            return redirect('/dashboard')
    else:
        meetings = Meeting.objects.all()
        hosts = Host.objects.all()
        return render(request, 'meeting_list.html', {'meetings': meetings, 'hosts': hosts})

# -------------------------------------------
# SAVE MEETING
# -------------------------------------------
@login_required(login_url='/admin_login/')
def save_meeting(request):
    if request.method == 'POST':
        host_name = request.POST.get('host')
        try:
            host = Host.objects.get(host_name=host_name)
        except Host.DoesNotExist:
            messages.error(request, 'Host does not exist.')
            return redirect('/dashboard')

        form = Meeting_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.time_in = timezone.now()
            instance.host = host
            instance.save()  # 🚀 This handles queue + notifies first visitor automatically

            rec = [host.host_email] if host.host_email else []
            subject = f"{instance.visitor_name} Checked In!"
            email(subject, instance, rec)

            messages.success(request, 'Information sent to Host. You will be called shortly!')
            return redirect('/dashboard')
        else:
            messages.error(request, 'Form error. Please correct it.')
            return redirect('/dashboard')
    return redirect('/dashboard')

# -------------------------------------------
# CHECKOUT MEETING
# -------------------------------------------
@login_required(login_url='/admin_login/')
def checkout(request):
    if request.method == 'GET':
        meeting_id = request.GET.get('mid')
        meeting = get_object_or_404(Meeting, id=meeting_id)

        if meeting.time_out:
            return HttpResponse(f"{meeting.visitor_name} already checked out!")

        meeting.checkout()  # ✅ Handles: mark completed, update queue, notify next
        send_checkout_email(meeting)

        return HttpResponse(f"{meeting.visitor_name} checked out successfully!")
    return HttpResponse("Invalid request method.")

# -------------------------------------------
# SEND CHECKOUT EMAIL
# -------------------------------------------
def send_checkout_email(meeting):
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    local_time_out = meeting.time_out.astimezone(nairobi_tz) if meeting.time_out else timezone.now().astimezone(nairobi_tz)

    subject = f"Visitor {meeting.visitor_name} Checked Out"
    message = (
        f"Dear {meeting.visitor_name},\n"
        f"You have successfully checked out at {local_time_out.strftime('%H:%M:%S')} "
        f"on {local_time_out.strftime('%Y-%m-%d')}."
    )
    recipient_list = [meeting.visitor_email] if meeting.visitor_email else []
    send_mail(subject, message, 'jkatunge13@gmail.com', recipient_list, fail_silently=False)

# -------------------------------------------
# GENERAL EMAIL FUNCTION
# -------------------------------------------
def email(subject, visitor, rec, host=None):
    sender = 'jkatunge13@gmail.com'
    html_content = render_to_string(
        'visitor_mail_template.html' if host else 'host_mail_template.html',
        {'visitor': visitor, 'host': host}
    )
    text_content = strip_tags(html_content)
    try:
        msg = EmailMultiAlternatives(subject, text_content, sender, rec)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"Email sent to: {rec}")
    except Exception as e:
        logging.error(f"Email error: {e}")
        print(f"Email error: {e}")

# -------------------------------------------
# HOST PROFILE MANAGER
# -------------------------------------------
@login_required(login_url='/admin_login/')
def profile_manager(request):
    if request.method == 'POST':
        form = Add_profile(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/dashboard')
    return redirect('/dashboard')

@login_required(login_url='/admin_login/')
def edit_profile(request):
    if request.method == 'POST':
        host_id = request.POST.get('editing')
        instance = Host.objects.filter(id=host_id).first()
        form = Add_profile(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('/dashboard')
    return redirect('/dashboard')

@login_required(login_url='/admin_login/')
def edit_delete(request):
    if request.method == 'POST':
        host_id = request.POST.get('id')
        host = Host.objects.filter(id=host_id).first()
        if host:
            if request.POST.get('edit'):
                form = Add_profile(instance=host)
                return render(request, 'profile_manager.html', {'form': form, 'edit': True, 'info': host_id})
            elif request.POST.get('delete'):
                host.delete()
                return redirect('/dashboard')
        else:
            messages.warning(request, 'Profile not found!')
            return redirect('/dashboard')
    return redirect('/dashboard')
