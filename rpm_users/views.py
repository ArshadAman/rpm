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
from django.contrib.auth.decorators import login_required
from django.contrib.admin.sites import site
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST

def home(request):
    """Homepage with options for moderator login and patient registration"""
    return render(request, 'home.html')

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
    ).order_by('-created_at')
    
    documentation_list = []
    for doc in documentations:
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
            'updated_at': doc.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Only add file_url if the file exists
        if doc.file and hasattr(doc.file, 'url'):
            doc_data['file_url'] = doc.file.url
        else:
            doc_data['file_url'] = None
            
        documentation_list.append(doc_data)
        print(documentation_list)
    
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
    sg = sendgrid.SendGridAPIClient(api_key="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")
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
