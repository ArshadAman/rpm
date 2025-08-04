from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings

from reports.models import Reports, Documentation
from reports.serializers import ReportSerializer
from reports.forms import ReportForm
from .models import Patient, Moderator, PastMedicalHistory, Interest, InterestPastMedicalHistory, InterestLead, Doctor
from retell_calling.models import CallSummary
from django.db import models
from .serializers import PatientSerializer, ModeratorSerializer
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .form import DocumentationForm
from .forms import PatientForm

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.sites import site
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST

def home(request):
    """Homepage with options for moderator login and patient registration"""
    return render(request, 'home.html')

def admin_access(request):
    """Check if user is admin and redirect appropriately"""
    if request.user.is_authenticated and request.user.is_superuser:
        # User is authenticated and is a superuser, redirect to admin dashboard
        return redirect('admin_dashboard')
    else:
        # User is not authenticated or not a superuser, redirect to admin login
        return redirect('/admin/')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_dashboard(request):
    """Admin dashboard with three main action sections"""
    try:
        # Get counts for dashboard display
        moderator_count = Moderator.objects.count()
        doctor_count = Doctor.objects.count()
        patient_count = Patient.objects.count()
        call_summary_count = CallSummary.objects.count()
        
        context = {
            'moderator_count': moderator_count,
            'doctor_count': doctor_count,
            'patient_count': patient_count,
            'call_summary_count': call_summary_count,
        }
        
        return render(request, 'admin_dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading admin dashboard: {str(e)}')
        return redirect('home')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def moderator_list(request):
    """Display list of all moderators with search and filtering capabilities"""
    try:
        # Get search query from request
        search_query = request.GET.get('search', '').strip()
        
        # Start with all moderators
        moderators = Moderator.objects.select_related('user').all()
        
        # Apply search filter if provided
        if search_query:
            moderators = moderators.filter(
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query) |
                models.Q(user__email__icontains=search_query) |
                models.Q(user__username__icontains=search_query) |
                models.Q(phone_number__icontains=search_query)
            )
        
        # Order by username for consistent display
        moderators = moderators.order_by('user__username')
        
        # Add patient count for each moderator
        moderators_with_counts = []
        for moderator in moderators:
            patient_count = Patient.objects.filter(moderator_assigned=moderator).count()
            moderators_with_counts.append({
                'moderator': moderator,
                'patient_count': patient_count
            })
        
        context = {
            'moderators_with_counts': moderators_with_counts,
            'search_query': search_query,
            'total_count': len(moderators_with_counts)
        }
        
        return render(request, 'admin/moderator_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading moderator list: {str(e)}')
        return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def moderator_create(request):
    """Create a new moderator with form handling and validation"""
    if request.method == 'POST':
        from .forms import ModeratorForm
        form = ModeratorForm(request.POST)
        
        if form.is_valid():
            try:
                # Create the User object
                user = User.objects.create(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                user.set_password(form.cleaned_data['password'])
                user.save()
                
                # Create the Moderator object
                moderator = Moderator.objects.create(
                    user=user,
                    phone_number=form.cleaned_data['phone_number']
                )
                
                messages.success(request, f'Moderator "{user.get_full_name()}" created successfully.')
                return redirect('moderator_list')
                
            except Exception as e:
                messages.error(request, f'Error creating moderator: {str(e)}')
                # Clean up user if moderator creation failed
                if 'user' in locals():
                    user.delete()
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        from .forms import ModeratorForm
        form = ModeratorForm()
    
    context = {
        'form': form,
        'title': 'Create New Moderator',
        'action': 'Create'
    }
    
    return render(request, 'admin/moderator_form.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def moderator_edit(request, moderator_id):
    """Edit an existing moderator with form handling and validation"""
    moderator = get_object_or_404(Moderator, id=moderator_id)
    
    if request.method == 'POST':
        from .forms import ModeratorForm
        form = ModeratorForm(request.POST, instance=moderator)
        
        if form.is_valid():
            try:
                # Update the User object
                user = moderator.user
                user.username = form.cleaned_data['username']
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                
                # Update password if provided
                if form.cleaned_data['password']:
                    user.set_password(form.cleaned_data['password'])
                
                user.save()
                
                # Update the Moderator object
                moderator.phone_number = form.cleaned_data['phone_number']
                moderator.save()
                
                messages.success(request, f'Moderator "{user.get_full_name()}" updated successfully.')
                return redirect('moderator_list')
                
            except Exception as e:
                messages.error(request, f'Error updating moderator: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        from .forms import ModeratorForm
        form = ModeratorForm(instance=moderator)
    
    context = {
        'form': form,
        'title': f'Edit Moderator: {moderator.user.get_full_name()}',
        'action': 'Update',
        'moderator': moderator
    }
    
    return render(request, 'admin/moderator_form.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def moderator_delete(request, moderator_id):
    """Delete a moderator with confirmation and safety checks"""
    moderator = get_object_or_404(Moderator, id=moderator_id)
    
    # Check if moderator has assigned patients
    assigned_patients_count = Patient.objects.filter(moderator_assigned=moderator).count()
    
    if request.method == 'POST':
        if assigned_patients_count > 0:
            messages.error(request, 
                f'Cannot delete moderator "{moderator.user.get_full_name()}" because they have {assigned_patients_count} assigned patients. Please reassign these patients first.')
            return redirect('moderator_list')
        
        try:
            moderator_name = moderator.user.get_full_name()
            user = moderator.user
            
            # Delete the moderator (this will also delete the user due to CASCADE)
            moderator.delete()
            user.delete()
            
            messages.success(request, f'Moderator "{moderator_name}" deleted successfully.')
            return redirect('moderator_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting moderator: {str(e)}')
            return redirect('moderator_list')
    
    context = {
        'moderator': moderator,
        'assigned_patients_count': assigned_patients_count,
        'can_delete': assigned_patients_count == 0
    }
    
    return render(request, 'admin/moderator_confirm_delete.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def doctor_list(request):
    """Display list of all doctors with search and filtering capabilities"""
    try:
        # Get search query from request
        search_query = request.GET.get('search', '').strip()
        
        # Start with all doctors
        doctors = Doctor.objects.select_related('user').all()
        
        # Apply search filter if provided
        if search_query:
            doctors = doctors.filter(
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query) |
                models.Q(user__email__icontains=search_query) |
                models.Q(user__username__icontains=search_query) |
                models.Q(phone_number__icontains=search_query) |
                models.Q(specialization__icontains=search_query)
            )
        
        # Order by username for consistent display
        doctors = doctors.order_by('user__username')
        
        # Add escalated patient count for each doctor
        doctors_with_counts = []
        for doctor in doctors:
            escalated_patient_count = Patient.objects.filter(doctor_escalated=doctor).count()
            doctors_with_counts.append({
                'doctor': doctor,
                'escalated_patient_count': escalated_patient_count
            })
        
        context = {
            'doctors_with_counts': doctors_with_counts,
            'search_query': search_query,
            'total_count': len(doctors_with_counts)
        }
        
        return render(request, 'admin/doctor_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading doctor list: {str(e)}')
        return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def doctor_create(request):
    """Create a new doctor with form handling and validation"""
    if request.method == 'POST':
        from .forms import DoctorForm
        form = DoctorForm(request.POST)
        
        if form.is_valid():
            try:
                # Create the User object
                user = User.objects.create(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name']
                )
                user.set_password(form.cleaned_data['password'])
                user.save()
                
                # Create the Doctor object
                doctor = Doctor.objects.create(
                    user=user,
                    phone_number=form.cleaned_data['phone_number'],
                    specialization=form.cleaned_data['specialization']
                )
                
                messages.success(request, f'Doctor "{user.get_full_name()}" created successfully.')
                return redirect('doctor_list')
                
            except Exception as e:
                messages.error(request, f'Error creating doctor: {str(e)}')
                # Clean up user if doctor creation failed
                if 'user' in locals():
                    user.delete()
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        from .forms import DoctorForm
        form = DoctorForm()
    
    context = {
        'form': form,
        'title': 'Add New Doctor',
        'action': 'Create'
    }
    
    return render(request, 'admin/doctor_form.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def doctor_detail(request, doctor_id):
    """Display detailed information about a specific doctor"""
    try:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # Get escalated patients for this doctor
        escalated_patients = Patient.objects.filter(doctor_escalated=doctor).select_related('user', 'moderator_assigned')
        
        # Format patient data for display
        formatted_patients = []
        for patient in escalated_patients:
            formatted_patients.append({
                'patient': patient,
                'age': patient.age,
                'moderator_name': patient.moderator_assigned.user.get_full_name() if patient.moderator_assigned else 'Not assigned'
            })
        
        context = {
            'doctor': doctor,
            'escalated_patients': formatted_patients,
            'escalated_count': len(formatted_patients)
        }
        
        return render(request, 'admin/doctor_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading doctor details: {str(e)}')
        return redirect('doctor_list')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def doctor_edit(request, doctor_id):
    """Edit an existing doctor with form handling and validation"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    if request.method == 'POST':
        from .forms import DoctorForm
        form = DoctorForm(request.POST, instance=doctor)
        
        if form.is_valid():
            try:
                # Update the User object
                user = doctor.user
                user.username = form.cleaned_data['username']
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                
                # Update password if provided
                if form.cleaned_data['password']:
                    user.set_password(form.cleaned_data['password'])
                
                user.save()
                
                # Update the Doctor object
                doctor.phone_number = form.cleaned_data['phone_number']
                doctor.specialization = form.cleaned_data['specialization']
                doctor.save()
                
                messages.success(request, f'Doctor "{user.get_full_name()}" updated successfully.')
                return redirect('doctor_list')
                
            except Exception as e:
                messages.error(request, f'Error updating doctor: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        from .forms import DoctorForm
        form = DoctorForm(instance=doctor)
    
    context = {
        'form': form,
        'title': f'Edit Doctor: {doctor.user.get_full_name()}',
        'action': 'Update',
        'doctor': doctor
    }
    
    return render(request, 'admin/doctor_form.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def doctor_delete(request, doctor_id):
    """Delete a doctor with confirmation and safety checks"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Check if doctor has escalated patients
    escalated_patients_count = Patient.objects.filter(doctor_escalated=doctor).count()
    
    if request.method == 'POST':
        if escalated_patients_count > 0:
            messages.error(request, 
                f'Cannot delete doctor "{doctor.user.get_full_name()}" because they have {escalated_patients_count} escalated patients. Please reassign these patients first.')
            return redirect('doctor_list')
        
        try:
            doctor_name = doctor.user.get_full_name()
            user = doctor.user
            
            # Delete the doctor (this will also delete the user due to CASCADE)
            doctor.delete()
            user.delete()
            
            messages.success(request, f'Doctor "{doctor_name}" deleted successfully.')
            return redirect('doctor_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting doctor: {str(e)}')
            return redirect('doctor_list')
    
    context = {
        'doctor': doctor,
        'escalated_patients_count': escalated_patients_count,
        'can_delete': escalated_patients_count == 0
    }
    
    return render(request, 'admin/doctor_confirm_delete.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_patient_list(request):
    """Display list of all patients in the system for admin access"""
    try:
        # Get search query from request
        search_query = request.GET.get('search', '').strip()
        
        # Start with all patients
        patients = Patient.objects.select_related('user', 'moderator_assigned', 'doctor_escalated').all()
        
        # Apply search filter if provided
        if search_query:
            patients = patients.filter(
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query) |
                models.Q(user__email__icontains=search_query) |
                models.Q(phone_number__icontains=search_query) |
                models.Q(insurance__icontains=search_query) |
                models.Q(monitoring_parameters__icontains=search_query)
            )
        
        # Order by creation date (newest first)
        patients = patients.order_by('-created_at')
        
        # Format patient data for display
        formatted_patients = []
        for patient in patients:
            # Format medications into a list if they exist
            medications = []
            if patient.medications:
                medications = [med.strip() for med in patient.medications.split('\n') if med.strip()]

            # Format pharmacy info into structured data if it exists
            pharmacy_info = {}
            if patient.pharmacy_info:
                try:
                    lines = patient.pharmacy_info.split('\n')
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            pharmacy_info[key.strip()] = value.strip()
                except:
                    pharmacy_info = {'Details': patient.pharmacy_info}

            # Format allergies into a list if they exist
            allergies = []
            if patient.allergies:
                allergies = [allergy.strip() for allergy in patient.allergies.split(',') if allergy.strip()]

            # Format family history into structured sections if it exists
            family_history = []
            if patient.family_history:
                history_lines = patient.family_history.split('\n')
                for line in history_lines:
                    if line.strip():
                        family_history.append(line.strip())

            formatted_patient = {
                'patient': patient,
                'formatted_medications': medications,
                'formatted_pharmacy': pharmacy_info,
                'formatted_allergies': allergies,
                'formatted_family_history': family_history,
                'moderator_name': patient.moderator_assigned.user.get_full_name() if patient.moderator_assigned else 'Not assigned',
                'doctor_name': patient.doctor_escalated.user.get_full_name() if patient.doctor_escalated else 'Not escalated'
            }
            formatted_patients.append(formatted_patient)
        
        context = {
            'patient_obj': formatted_patients,
            'search_query': search_query,
            'total_count': len(formatted_patients),
            'is_admin_view': True
        }
        
        return render(request, 'admin/admin_patient_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading patient list: {str(e)}')
        return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_patient_detail(request, patient_id):
    """Display detailed patient information for admin access"""
    try:
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Get all reports for this patient
        reports = Reports.objects.filter(patient=patient).order_by('-created_at')
        
        # Get all doctors for potential escalation
        doctors = Doctor.objects.all()
        
        context = {
            'patient': patient,
            'reports': reports,
            'doctors': doctors,
            'is_admin_view': True
        }
        
        return render(request, 'index.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading patient details: {str(e)}')
        return redirect('admin_patient_list')

def express_interest(request):
    """Handle the express interest form for potential RPM leads"""
    # Get PMH choices for the form's select field
    pmh_choices = PastMedicalHistory.PMH_CHOICES
    
    if request.method == 'POST':
        # Process form submission
        form_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone_number': request.POST.get('phone_number'),
            'date_of_birth': request.POST.get('date_of_birth'),
            'age': request.POST.get('age'),
            'allergies': request.POST.get('allergies'),
            'insurance': request.POST.get('insurance'),
            'service_interest': request.POST.get('service_interest'),
            'additional_comments': request.POST.get('additional_comments'),
            'good_eyesight': 'good_eyesight' in request.POST,
            'can_follow_instructions': 'can_follow_instructions' in request.POST,
            'can_take_readings': 'can_take_readings' in request.POST,
        }
        
        # Get past medical history selections
        past_medical_history = request.POST.getlist('past_medical_history')
        
        try:
            # Create the Interest record
            interest = Interest.objects.create(**form_data)
            
            # Add past medical history entries
            for pmh in past_medical_history:
                InterestPastMedicalHistory.objects.create(
                    interest=interest,
                    pmh=pmh
                )
            
            messages.success(request, "Thank you for your interest! We'll be in touch soon.")
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f"There was an error processing your form: {str(e)}")
            return render(request, 'express_interest.html', {
                'pmh_choices': pmh_choices,
                'form_data': form_data
            })
    
    # GET request - display the form
    return render(request, 'express_interest.html', {
        'pmh_choices': pmh_choices
    })

@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def create_patient(request):
    # check if the patient is already in the sso, and if the patient is in the sso, then check if the patient is already in the database and if the user in the database then return the patient object and if the user is not in the database then create new patient object, and if the user is not in sso then create the user in the sso and also in the database

    data = request.data
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    entered_otp = data.get("entered_otp")
    phone_number = data.get("phone_number")
    date_of_birth = data.get('date_of_birth')
    height = data.get('height')
    weight = data.get('weight')
    
    print("Number")

    # check if the patient is already in the sso
    response = requests.post("https://auth.pinksurfing.com/api/signup/", data=data)
    if response.status_code == 409:
        return Response(
            {"error": response.text},
            status=status.HTTP_409_CONFLICT,
        )
    elif response.status_code != 201:
        return Response(
            {"error": response.text},
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        # check if the patient is already in the database
        user = User.objects.filter(username = email).first()
        patient = Patient.objects.filter(user=user).first()
        if patient:
            return Response(
                {"message": "User already exists"}, status=status.HTTP_409_CONFLICT
            )
        else:
            # create new patient object
            user = User.objects.create(
                username=email,
                first_name=first_name,
                last_name=last_name,
                email=email,  # Use the same email as in the SSO for the local user
            )
            user.set_password(password)  # Properly hash the password
            user.save()
            patient = Patient.objects.create(
                user = user,
                date_of_birth=date_of_birth, 
                height=height,
                weight=weight,
            )
            return Response(
                {"message": "Patient successfully created"},
                status=status.HTTP_201_CREATED,
            )

@api_view(['POST'])            
def assign_patient(request, patient_id, moderator_id=""):
    patient = Patient.objects.get(id=patient)
    moderator = Moderator.objects.get(id=moderator_id)
    patient.moderator_assigned = moderator
    patient.save()
    return Response({"success": True}, status=status.HTTP_200_OK)
    
def moderator_actions_view(request, patient_id):
    # Get the moderator based on the email from the request (ensure authentication handles this)
    
    user = request.user  # Assuming user is authenticated and their email is available in request.user
    moderator = get_object_or_404(Moderator, user=user)
    patient = get_object_or_404(Patient, id=patient_id)

    context = {
        'patient': patient,
        'moderator': moderator,
    }
    action = request.GET.get('action')

    if action == 'access'.lower() and patient.moderator_assigned == moderator or request.user.is_superuser:
        # Access patient details
        reports = Reports.objects.filter(patient=patient)
        context['reports'] = reports  # Add patient details to the context
        context['doctors'] = Doctor.objects.all()  # Pass all doctors for escalation dropdown
        print(context['doctors'], "DEBUG: Doctors available for escalation")
        return render(request, 'index.html', context)

    elif action == 'update'.lower():
        if request.method == 'POST':
            # Handle form submission for updating the patient
            form = PatientForm(request.POST, instance=patient)
            if form.is_valid():
                form.save()
                context['patient_details'] = patient  # Updated patient
                context['success'] = 'Patient updated successfully'
            else:
                context['form_errors'] = form.errors
        else:
            # Prepopulate the form with patient data for rendering
            form = PatientForm(instance=patient)
            context['form'] = form

        return render(request, 'index.html', context)

    elif action == 'delete':
        # Delete patient
        patient.delete()
        context['success'] = 'Patient deleted successfully'
        return render(request, 'index.html', context)

    elif action == 'update-report':
        report_id = request.POST.get('report_id')
        report = get_object_or_404(Reports, id=report_id)

        if report.patient != patient:
            context['error'] = "This report does not belong to this patient."
            return render(request, 'index.html', context)

        if request.method == 'POST':
            # Handle report update
            form = ReportForm(request.POST, instance=report)
            if form.is_valid():
                form.save()
                context['success'] = "Report updated successfully"
                context['report'] = report
            else:
                context['form_errors'] = form.errors
        else:
            # Prepopulate the report form for updating
            form = ReportForm(instance=report)
            context['form'] = form

        return render(request, 'index.html', context)

    elif action == 'delete-report':
        report_id = request.POST.get('report_id')
        report = get_object_or_404(Reports, id=report_id)

        if report.patient != patient:
            context['error'] = "This report does not belong to this patient."
        else:
            report.delete()
            context['success'] = "Report deleted successfully"

        return render(request, 'index.html', context)

    else:
        # Invalid action
        context['error'] = "Invalid action."
        return render(request, 'index.html', context)

    
def all_moderators(request):
    moderators = Moderator.objects.all()
    serializer = ModeratorSerializer(moderators, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_patient(request, patient_id):
    pass

def moderator_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if the user is a moderator
            if hasattr(user, 'moderator'):
                login(request, user)
                return redirect('view_all_assigned_patient')  # Redirect to moderator dashboard or home page
            else:
                messages.error(request, 'You are not authorized as a moderator.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'moderator_login.html')

def moderator_logout(request):
    logout(request)  # Logs out the current user
    return redirect('/')  # Redirect to the login page after logout

@login_required
def view_assigned_patient(request):
    moderator = Moderator.objects.get(user=request.user)
    patient_obj = Patient.objects.filter(moderator_assigned=moderator)
    
    formatted_patients = []
    for patient in patient_obj:
        # Format medications into a list if they exist
        medications = []
        if patient.medications:
            medications = [med.strip() for med in patient.medications.split('\n') if med.strip()]

        # Format pharmacy info into structured data if it exists
        pharmacy_info = {}
        if patient.pharmacy_info:
            try:
                lines = patient.pharmacy_info.split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        pharmacy_info[key.strip()] = value.strip()
            except:
                pharmacy_info = {'Details': patient.pharmacy_info}

        # Format allergies into a list if they exist
        allergies = []
        if patient.allergies:
            allergies = [allergy.strip() for allergy in patient.allergies.split(',') if allergy.strip()]

        # Format family history into structured sections if it exists
        family_history = []
        if patient.family_history:
            history_lines = patient.family_history.split('\n')
            for line in history_lines:
                if line.strip():
                    family_history.append(line.strip())

        formatted_patient = {
            'patient': patient,
            'formatted_medications': medications,
            'formatted_pharmacy': pharmacy_info,
            'formatted_allergies': allergies,
            'formatted_family_history': family_history
        }
        formatted_patients.append(formatted_patient)

    context = {
        'patient_obj': formatted_patients,
    }
    return render(request, 'view_assigned_patient.html', context)

@login_required
def write_document(request, report_id):
    report = Reports.objects.get(id=report_id)
    if request.method == 'POST':
        form = DocumentationForm(request.POST, request.FILES)
        if form.is_valid():
            # Pass the current user to the form's save method to set the 'written_by' field
            document = form.save(commit=False, user=request.user)
            document.report = report
            document.save()
            messages.success(request, 'Documentation saved successfully.')
            # Redirect to the view documentation page for this patient
            return redirect('view_documentation', patient_id=report.patient.id)
    else:
        form = DocumentationForm()
    
    # Get the patient related to the report to pass to the template
    patient = report.patient
    
    return render(request, 'reports/add_docs.html', {'form': form, 'report': report, 'patient': patient}) # Render add_docs.html

@login_required
def view_documentation(request, patient_id):
    # Check if the user is a moderator
    user = request.user
    is_moderator = Moderator.objects.filter(user=user).exists()
    patient = Patient.objects.filter(id=patient_id).first()
    is_patient = Patient.objects.filter(user=user, id=patient_id).exists()
    print(f"DEBUG: Patient = {patient}")
    
    # Allow access if user is a moderator or if the user is the patient
    if not is_moderator and not is_patient:
        print("DEBUG: User is not authorized to view documentation")
        return JsonResponse({"error": "You are not authorized to view this documentation"}, status=403)
      # Get documentation for the patient
    patient = get_object_or_404(Patient, id=patient_id)
    
    documentations = Documentation.objects.filter(
        patient=patient,
    ).order_by('-doc_report_date')
    documentation_list = []
    for doc in documentations:
        print("fldsaf",doc.doc_report_date)
        doc_data = {
            'id': doc.id,
            'title': doc.title,
            'history_of_present_illness': doc.history_of_present_illness,
            'chief_complaint': doc.chief_complaint,
            'subjective': doc.subjective,
            'objective': doc.objective,
            'assessment': doc.assessment,
            'plan': doc.plan,
            'written_by': doc.written_by,
            'created_at': doc.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': doc.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            'doc_report_date': doc.doc_report_date.strftime("%m/%d/%Y") if doc.doc_report_date else None,
        }
        
        # Only add file_url if the file exists
        if doc.file and hasattr(doc.file, 'url'):
            doc_data['file_url'] = doc.file.url
        else:
            doc_data['file_url'] = None
            
        documentation_list.append(doc_data)
        print(documentation_list)
    print('DEBUG: Documentation List:', documentation_list)

    return JsonResponse({'documentations': documentation_list})


@login_required
def register_patient(request):
    if request.method == 'POST':
        data = {
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'first_name': request.POST.get('first_name'), 
            'last_name': request.POST.get('last_name'),
            'phone_number': request.POST.get('phone_number'),
            'date_of_birth': request.POST.get('date_of_birth'),
            'height': request.POST.get('height'),
            'weight': request.POST.get('weight'),
            'insurance': request.POST.get('insurance'),
            'insurance_number': request.POST.get('insurance_number'),
            'sex': request.POST.get('sex'),
            'monitoring_parameters': request.POST.get('monitoring_parameters'),
            'device_serial_number': request.POST.get('device_serial_number'),
            'pharmacy_info': request.POST.get('pharmacy_info'),
            'allergies': request.POST.get('allergies'),
            'drink': request.POST.get('drink', 'NO'),
            'smoke': request.POST.get('smoke', 'NO'),
            'family_history': request.POST.get('family_history'),
            'medications': request.POST.get('medications'),
            'past_medical_history': request.POST.getlist('past_medical_history', [])
        }

        # Check if patient already exists
        if User.objects.filter(username=data['email']).exists():
            messages.error(request, 'Patient with this email already exists')
            return render(request, 'register_patient.html')

        # Create local user and patient
        try:
            user = User.objects.create(
                username=data['email'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
            )
            user.set_password(data['password'])  # Properly hash the password
            user.save()
            
            patient = Patient.objects.create(
                user=user,
                date_of_birth=data['date_of_birth'],
                height=data['height'],
                weight=data['weight'],
                insurance=data['insurance'],
                insurance_number=data['insurance_number'],
                sex=data['sex'],
                phone_number=data['phone_number'],
                monitoring_parameters=data['monitoring_parameters'],
                device_serial_number=data['device_serial_number'] if data['device_serial_number'] else None,
                pharmacy_info=data['pharmacy_info'] if data['pharmacy_info'] else None,
                allergies=data['allergies'] if data['allergies'] else None,
                drink=data['drink'],
                smoke=data['smoke'],
                family_history=data['family_history'] if data['family_history'] else None,
                medications=data['medications'] if data['medications'] else None
            )

            # Create past medical history records
            for pmh in data['past_medical_history']:
                PastMedicalHistory.objects.create(
                    patient=patient,
                    pmh=pmh
                )

            # Assign the current moderator
            moderator = Moderator.objects.get(user=request.user)
            patient.moderator_assigned = moderator
            patient.save()

            messages.success(request, 'Patient registered successfully')
            return redirect('view_all_assigned_patient')

        except ValueError as e:
            messages.error(request, str(e))  # This will catch the BMI calculation error
            return render(request, 'register_patient.html')
        except Exception as e:
            messages.error(request, f'Error creating patient: {str(e)}')
            return render(request, 'register_patient.html')

    context = {
        'sex_choices': Patient.SEX_CHOICES,
        'monitoring_choices': Patient.MONITORING_CHOICES,
        'pmh_choices': PastMedicalHistory.PMH_CHOICES
    }
    return render(request, 'register_patient.html', context)

def registration_success(request):
    return render(request, 'registration_success.html')

def patient_self_registration(request):
    if request.method == 'POST':
        data = {
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'first_name': request.POST.get('first_name'), 
            'last_name': request.POST.get('last_name'),
            'phone_number': request.POST.get('phone_number'),
            'date_of_birth': request.POST.get('date_of_birth'),
            'height': request.POST.get('height'),
            'weight': request.POST.get('weight'),
            'insurance': request.POST.get('insurance'),
            'insurance_number': request.POST.get('insurance_number'),
            'sex': request.POST.get('sex'),
            'monitoring_parameters': request.POST.get('monitoring_parameters'),
            'device_serial_number': request.POST.get('device_serial_number'),
            'pharmacy_info': request.POST.get('pharmacy_info'),
            'allergies': request.POST.get('allergies'),
            'drink': request.POST.get('drink', 'NO'),
            'smoke': request.POST.get('smoke', 'NO'),
            'family_history': request.POST.get('family_history'),
            'medications': request.POST.get('medications'),
            'past_medical_history': request.POST.getlist('past_medical_history', [])
        }

        # Check if patient already exists
        if User.objects.filter(username=data['email']).exists():
            messages.error(request, 'Patient with this email already exists')
            return render(request, 'patient_self_register.html')

        # Create local user and patient
        try:
            user = User.objects.create(
                username=data['email'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
            )
            user.set_password(data['password'])  # Properly hash the password
            user.save()
            
            patient = Patient.objects.create(
                user=user,
                date_of_birth=data['date_of_birth'],
                height=data['height'],
                weight=data['weight'],
                insurance=data['insurance'],
                insurance_number=data['insurance_number'],
                sex=data['sex'],
                phone_number=data['phone_number'],
                monitoring_parameters=data['monitoring_parameters'],
                device_serial_number=data['device_serial_number'] if data['device_serial_number'] else None,
                pharmacy_info=data['pharmacy_info'] if data['pharmacy_info'] else None,
                allergies=data['allergies'] if data['allergies'] else None,
                drink=data['drink'],
                smoke=data['smoke'],
                family_history=data['family_history'] if data['family_history'] else None,
                medications=data['medications'] if data['medications'] else None
            )

            # Create past medical history records
            for pmh in data['past_medical_history']:
                PastMedicalHistory.objects.create(
                    patient=patient,
                    pmh=pmh
                )

            messages.success(request, 'Patient registered successfully')
            return redirect('registration_success')

        except ValueError as e:
            messages.error(request, str(e))  # This will catch the BMI calculation error
            return render(request, 'patient_self_register.html')
        except Exception as e:
            messages.error(request, f'Error creating patient: {str(e)}')
            return render(request, 'patient_self_register.html')

    context = {
        'sex_choices': Patient.SEX_CHOICES,
        'monitoring_choices': Patient.MONITORING_CHOICES,
        'pmh_choices': PastMedicalHistory.PMH_CHOICES
    }
    return render(request, 'patient_self_register.html', context)


@login_required
def view_patient(request, patient_id):
    patient = Patient.objects.get(id=patient_id)
    
    # Process allergies
    allergies_list = []
    if patient.allergies:
        allergies_list = [allergy.strip() for allergy in patient.allergies.split(',')]
    
    # Process medications
    medications_list = []
    if patient.medications:
        medications_list = [med.strip() for med in patient.medications.split('\n')]
    
    # Process family history
    family_history_list = []
    if patient.family_history:
        family_history_list = [history.strip() for history in patient.family_history.split('\n')]
    
    # Process pharmacy info
    pharmacy_info_list = []
    if patient.pharmacy_info:
        pharmacy_info_list = [info.strip() for info in patient.pharmacy_info.split('\n')]
    
    context = {
        'patient': patient,
        'allergies_list': allergies_list,
        'medications_list': medications_list,
        'family_history_list': family_history_list,
        'pharmacy_info_list': pharmacy_info_list,
    }
    return render(request, 'index.html', context)

@never_cache
@login_required
def admin_logout(request):
    """Custom admin logout view that handles both GET and POST requests"""
    logout(request)
    return redirect('admin:login')

def patient_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt - Username: {username}")
        print(f"Login attempt - Password: {password}")
        
        user = authenticate(request, username=username, password=password)
        print(f"User: {user}")  # Debug print
        
        if user is not None:
            # Check if user is a moderator
            if Moderator.objects.filter(user=user).exists():
                print("User is a moderator, redirecting to moderator login")
                return JsonResponse({
                    'success': False,
                    'error': 'Please use the moderator login page'
                })
            
            # Check if user is a patient
            try:
                patient = Patient.objects.get(user=user)
                print(f"Found patient: {patient}")  # Debug print
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/patient_home/'
                })
            except Patient.DoesNotExist:
                print("User exists but no associated patient found")  # Debug print
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid credentials'
                })
        else:
            print("Authentication failed - user is None")  # Debug print
            return JsonResponse({
                'success': False,
                'error': 'Invalid credentials'
            })
    
    return render(request, 'reports/patient_login.html')

@login_required
def patient_home(request):
    try:
        patient = Patient.objects.get(user=request.user)
        reports = Reports.objects.filter(patient=patient).order_by('-created_at')
        context = {
            'patient': patient,
            'reports': reports
        }
        return render(request, 'reports/patient_home.html', context)
    except Patient.DoesNotExist:
        logout(request)
        return redirect('patient_login')

def patient_logout(request):
    logout(request)
    return redirect('home')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        print(f"User: {user}")  # Debug print
        if user is not None:
            login(request, user)
            return redirect('admin:index')
        else:
            # Handle invalid login
            return render(request, 'admin/login.html', {'error': 'Invalid username or password'})
    return render(request, 'admin/login.html')

@csrf_exempt
def track_interest(request):
    if request.method == "POST":
        try:
            # Ensure the user has a session
            if not request.session.session_key:
                request.session.save()
            session_key = request.session.session_key

            data = json.loads(request.body)
            lead = InterestLead.objects.filter(session_key=session_key).first()
            if not lead:
                lead = InterestLead.objects.create(session_key=session_key)

            for field in [
                "first_name", "last_name", "email", "phone_number", "date_of_birth", "age",
                "allergies", "service_interest", "insurance",
                "good_eyesight", "can_follow_instructions", "can_take_readings", "additional_comments"
            ]:
                if field in data:
                    value = data[field]
                    if field == "date_of_birth" and value == "":
                        value = None
                    if field == "age" and (value == "" or value is None):
                        value = None
                    setattr(lead, field, value)
            lead.save()
            return JsonResponse({"success": True, "lead_id": lead.id})
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)

def terms_and_conditions_view(request):
    """Renders the terms and conditions page."""
    return render(request, 'terms_and_conditions.html')

@login_required
def edit_documentation(request, doc_id):
    documentation = Documentation.objects.get(id=doc_id)
    report = documentation.report if hasattr(documentation, 'report') else None
    if request.method == 'POST':
        form = DocumentationForm(request.POST, request.FILES, instance=documentation)
        if form.is_valid():
            document = form.save(commit=False, user=request.user)
            if report:
                document.report = report
            document.save()
            messages.success(request, 'Documentation updated successfully.')
            return redirect('view_documentation', patient_id=documentation.patient.id)
    else:
        form = DocumentationForm(instance=documentation, initial={
            'full_documentation': documentation.history_of_present_illness
        })
    patient = documentation.patient
    return render(request, 'reports/add_docs.html', {'form': form, 'reports': report, 'patient': patient, 'edit_mode': True, 'doc_id': doc_id})

def doctor_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and Doctor.objects.filter(user=user).exists():
            login(request, user)
            return redirect('view_escalated_patient')
        else:
            messages.error(request, 'Invalid credentials or not a doctor.')
    return render(request, 'doctor_login.html')

@login_required
def view_escalated_patient(request):
    # Only allow doctors
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        logout(request)
        return redirect('doctor_login')
    # List all escalated patients assigned to this doctor
    patients = Patient.objects.filter(doctor_escalated=doctor, is_escalated=True)
    formatted_patients = []
    for patient in patients:
        medications = [med.strip() for med in patient.medications.split('\n')] if patient.medications else []
        allergies = [allergy.strip() for allergy in patient.allergies.split(',')] if patient.allergies else []
        family_history = [fh.strip() for fh in patient.family_history.split('\n')] if patient.family_history else []
        pharmacy_info = [info.strip() for info in patient.pharmacy_info.split('\n')] if patient.pharmacy_info else []
        formatted_patients.append({
            'patient': patient,
            'formatted_medications': medications,
            'formatted_allergies': allergies,
            'formatted_family_history': family_history,
            'formatted_pharmacy': pharmacy_info,
        })
    context = {
        'patients': formatted_patients,
    }
    print(context, "DEBUG: Escalated patients context")
    return render(request, 'view_escalated_patient.html', context)

@login_required
def doctor_patient_detail(request, patient_id):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        logout(request)
        return redirect('doctor_login')
    patient = get_object_or_404(Patient, id=patient_id, doctor_escalated=doctor, is_escalated=True)

    # Format medications into a list if they exist
    medications = []
    if patient.medications:
        medications = [med.strip() for med in patient.medications.split('\n') if med.strip()]

    # Format pharmacy info into structured data if it exists
    pharmacy_info = {}
    if patient.pharmacy_info:
        try:
            lines = patient.pharmacy_info.split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    pharmacy_info[key.strip()] = value.strip()
        except:
            pharmacy_info = {'Details': patient.pharmacy_info}

    # Format allergies into a list if they exist
    allergies = []
    if patient.allergies:
        allergies = [allergy.strip() for allergy in patient.allergies.split(',') if allergy.strip()]

    # Format family history into structured sections if it exists
    family_history = []
    if patient.family_history:
        history_lines = patient.family_history.split('\n')
        for line in history_lines:
            if line.strip():
                family_history.append(line.strip())

    context = {
        'patient': patient,
        'formatted_medications': medications,
        'formatted_pharmacy': pharmacy_info,
        'formatted_allergies': allergies,
        'formatted_family_history': family_history
    }
    return render(request, 'index.html', context)

def doctor_logout(request):
    logout(request)
    return redirect('doctor_login')



# Escalation logic
@login_required
@require_POST
def escalate_patient(request, patient_id):
    moderator = get_object_or_404(Moderator, user=request.user)
    patient = get_object_or_404(Patient, id=patient_id, moderator_assigned=moderator)
    doctor_id = request.POST.get('doctor_id')
    doctor = get_object_or_404(Doctor, id=doctor_id)
    patient.doctor_escalated = doctor
    patient.is_escalated = True
    patient.save()

    # SendGrid email notification to doctor
    sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    doctor_email = doctor.user.email
    patient_user = patient.user
    message = Mail(
        from_email='marketing@pinksurfing.com',
        to_emails=doctor_email,
        subject='A Patient Has Been Escalated to You',
        html_content=f"""
        <h3>Patient Escalation Notification</h3>
        <p>Dear Dr. {doctor.user.get_full_name() or doctor.user.username},</p>
        <p>The following patient has been escalated to you:</p>
        <ul>
            <li><strong>Name:</strong> {patient_user.first_name} {patient_user.last_name}</li>
            <li><strong>Email:</strong> {patient_user.email}</li>
            <li><strong>Date of Birth:</strong> {patient.date_of_birth}</li>
            <li><strong>Sex:</strong> {patient.sex}</li>
            <li><strong>Phone Number:</strong> {patient.phone_number}</li>
            <li><strong>Insurance:</strong> {patient.insurance}</li>
            <li><strong>Allergies:</strong> {patient.allergies or "N/A"}</li>
            <li><strong>Medications:</strong> {patient.medications or "N/A"}</li>
            <li><strong>Family History:</strong> {patient.family_history or "N/A"}</li>
        </ul>
        <p>Please log in to the portal to view more details.</p>
        """
    )
    try:
        sg.send(message)
    except Exception as e:
        print("SendGrid error:", e)

    messages.success(request, f"Patient escalated to Dr. {doctor.user.get_full_name()}")
    return redirect('moderator_actions', patient_id=patient.id)

# Admin-verified user creation views
def admin_create_user(request):
    """Display form for creating moderator or doctor accounts with admin verification"""
    return render(request, 'admin_create_user.html')

def test_staff_ui(request):
    """Test page for staff creation workflow"""
    with open('/app/test_staff_ui.html', 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/html')

@csrf_exempt
def verify_admin_password(request):
    """Verify admin password before allowing user creation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_password = data.get('admin_password')
            
            # Get the first superuser for authentication
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if not admin_user:
                return JsonResponse({
                    'success': False,
                    'error': 'No admin user found in the system.'
                })
            
            # Check if the provided password is correct
            if admin_user.check_password(admin_password):
                return JsonResponse({
                    'success': True,
                    'message': 'Admin password verified successfully.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid admin password.'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data.'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })

def create_staff_user(request):
    """Create moderator or doctor account after admin verification"""
    print(f"DEBUG: create_staff_user called with method: {request.method}")
    print(f"DEBUG: Content type: {request.content_type}")
    
    if request.method == 'POST':
        try:
            print("DEBUG: Processing POST request for staff user creation")
            
            # Verify admin password first
            admin_password = request.POST.get('admin_password')
            print(f"DEBUG: Admin password provided: {'Yes' if admin_password else 'No'}")
            
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if not admin_user or not admin_user.check_password(admin_password):
                print("DEBUG: Admin password verification failed")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid admin password.'
                })
            
            print("DEBUG: Admin password verified successfully")
            
            # Get form data
            user_type = request.POST.get('user_type')  # 'moderator' or 'doctor'
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone_number = request.POST.get('phone_number')
            
            print(f"DEBUG: Form data - user_type: {user_type}, username: {username}, email: {email}")
            
            # Additional fields for doctor
            specialization = request.POST.get('specialization') if user_type == 'doctor' else None
            
            # Validation
            if not all([user_type, username, email, password, first_name, last_name]):
                return JsonResponse({
                    'success': False,
                    'error': 'All required fields must be filled.'
                })
            
            if user_type not in ['moderator', 'doctor']:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid user type.'
                })
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Username already exists.'
                })
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Email already exists.'
                })
            
            # Create user
            print(f"DEBUG: Creating {user_type} user")
            if user_type == 'moderator':
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True  # Moderators are staff users
                )
                print(f"DEBUG: User created with ID: {user.id}")
                
                # Create moderator profile
                moderator = Moderator.objects.create(
                    user=user,
                    phone_number=phone_number or ''
                )
                print(f"DEBUG: Moderator profile created with ID: {moderator.id}")
                
                success_message = f'Moderator account created successfully for {first_name} {last_name}.'
                
            elif user_type == 'doctor':
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                print(f"DEBUG: Doctor user created with ID: {user.id}")
                
                # Create doctor profile
                doctor = Doctor.objects.create(
                    user=user,
                    specialization=specialization or '',
                    phone_number=phone_number or ''
                )
                print(f"DEBUG: Doctor profile created with ID: {doctor.id}")
                
                success_message = f'Doctor account created successfully for Dr. {first_name} {last_name}.'
            
            print(f"DEBUG: Returning success response: {success_message}")
            return JsonResponse({
                'success': True,
                'message': success_message
            })
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })


# Moderator Shortcut API Views
@login_required
def get_shortcuts(request):
    """Get all shortcuts for the current moderator"""
    try:
        moderator = get_object_or_404(Moderator, user=request.user)
        from .models import ModeratorShortcut
        shortcuts = ModeratorShortcut.objects.filter(moderator=moderator)
        shortcuts_data = [
            {
                'id': shortcut.id,
                'shortcut_key': shortcut.shortcut_key,
                'description': shortcut.description,
                'content': shortcut.content
            }
            for shortcut in shortcuts
        ]
        return JsonResponse({'shortcuts': shortcuts_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def create_shortcut(request):
    """Create a new shortcut for the current moderator"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        moderator = get_object_or_404(Moderator, user=request.user)
        from .models import ModeratorShortcut
        
        data = json.loads(request.body)
        shortcut_key = data.get('shortcut_key', '').strip()
        description = data.get('description', '').strip()
        content = data.get('content', '').strip()
        
        if not all([shortcut_key, description, content]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        # Check if shortcut already exists for this moderator
        if ModeratorShortcut.objects.filter(moderator=moderator, shortcut_key=shortcut_key).exists():
            return JsonResponse({'error': 'Shortcut key already exists'}, status=400)
        
        shortcut = ModeratorShortcut.objects.create(
            moderator=moderator,
            shortcut_key=shortcut_key,
            description=description,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'shortcut': {
                'id': shortcut.id,
                'shortcut_key': shortcut.shortcut_key,
                'description': shortcut.description,
                'content': shortcut.content
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def update_shortcut(request, shortcut_id):
    """Update an existing shortcut"""
    if request.method != 'PUT':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        moderator = get_object_or_404(Moderator, user=request.user)
        from .models import ModeratorShortcut
        shortcut = get_object_or_404(ModeratorShortcut, id=shortcut_id, moderator=moderator)
        
        data = json.loads(request.body)
        shortcut_key = data.get('shortcut_key', '').strip()
        description = data.get('description', '').strip()
        content = data.get('content', '').strip()
        
        if not all([shortcut_key, description, content]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        # Check if new shortcut key conflicts with existing ones (excluding current)
        if (shortcut_key != shortcut.shortcut_key and 
            ModeratorShortcut.objects.filter(moderator=moderator, shortcut_key=shortcut_key).exists()):
            return JsonResponse({'error': 'Shortcut key already exists'}, status=400)
        
        shortcut.shortcut_key = shortcut_key
        shortcut.description = description
        shortcut.content = content
        shortcut.save()
        
        return JsonResponse({
            'success': True,
            'shortcut': {
                'id': shortcut.id,
                'shortcut_key': shortcut.shortcut_key,
                'description': shortcut.description,
                'content': shortcut.content
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def delete_shortcut(request, shortcut_id):
    """Delete a shortcut"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        moderator = get_object_or_404(Moderator, user=request.user)
        from .models import ModeratorShortcut
        shortcut = get_object_or_404(ModeratorShortcut, id=shortcut_id, moderator=moderator)
        shortcut.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def search_shortcuts(request):
    """Search shortcuts by key for autocomplete"""
    try:
        moderator = get_object_or_404(Moderator, user=request.user)
        from .models import ModeratorShortcut
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse({'shortcuts': []})
        
        shortcuts = ModeratorShortcut.objects.filter(
            moderator=moderator,
            shortcut_key__icontains=query
        )[:10]  # Limit to 10 results
        
        shortcuts_data = [
            {
                'shortcut_key': shortcut.shortcut_key,
                'description': shortcut.description,
                'content': shortcut.content
            }
            for shortcut in shortcuts
        ]
        return JsonResponse({'shortcuts': shortcuts_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
