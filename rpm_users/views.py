from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
from django.utils.timezone import localtime

from reports.models import Reports, Documentation
from reports.serializers import ReportSerializer
from .models import Patient, Moderator, PastMedicalHistory
from .serializers import PatientSerializer, ModeratorSerializer
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .form import DocumentationForm

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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
    patient_obj = Patient.objects.filter(moderator_assigned = moderator)
    
    context = {
        'patient_obj': patient_obj,
    }
    return render(request, 'view_assigned_patient.html', context)

@login_required
def write_document(request, report_id):
    report = Reports.objects.get(id=report_id)
    if request.method == 'POST':
        form = DocumentationForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.report = report
            document.save()
            return redirect('view_all_assigned_patient')
    else:
        form = DocumentationForm()
    
    return render(request, 'write_document.html', {'form': form, 'report': report})

@login_required
def view_documentation(request):
    date = request.GET.get('date')
    moderator = Moderator.objects.get(user=request.user)
    patient_ids = Patient.objects.filter(moderator_assigned=moderator).values_list("id", flat=True)

    print(f"Filtering for date: {date}")  # Debugging Step

    if date:
        documentations = Documentation.objects.filter(report__patient__in=patient_ids, created_at__date=date)
    else:
        documentations = Documentation.objects.filter(report__patient__in=patient_ids)

    print(f"Found {documentations.count()} documentations")  # Debugging Step

    data = [
        {
            "title": doc.title,
            "description": doc.description,
            "chief_complaint": doc.chief_complaint,
            "subjective": doc.subjective,
            "objective": doc.objective,
            "assessment": doc.assessment,
            "plan": doc.plan,
            "file_url": doc.file.url if doc.file else None,
            "created_at": localtime(doc.created_at).strftime("%d-%m-%Y %I:%M %p"),
            "updated_at": localtime(doc.updated_at).strftime("%d-%m-%Y %I:%M %p"),
        }
        for doc in documentations
    ]

    return JsonResponse(data, safe=False)

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
            'sex': request.POST.get('sex'),
            'monitoring_parameters': request.POST.get('monitoring_parameters'),
            'device_serial_number': request.POST.get('device_serial_number'),
            'pharmacy_info': request.POST.get('pharmacy_info'),
            'allergies': request.POST.get('allergies'),
            'drink_smoke': request.POST.get('drink_smoke', 'NO'),
            'family_history': request.POST.get('family_history'),
            'medications': request.POST.get('medications'),
            'past_medical_history': request.POST.getlist('past_medical_history', [])
        }

        # Check if patient already exists
        if User.objects.filter(username=data['email']).exists():
            messages.error(request, 'Patient with this email already exists')
            return render(request, 'register_patient.html')

        # Create user in SSO
        # response = requests.post("https://auth.pinksurfing.com/api/signup/", data=data)
        # if response.status_code != 201:
        #     messages.error(request, 'Error creating user in SSO system')
        #     return render(request, 'register_patient.html')

        # Create local user and patient
        try:
            user = User.objects.create(
                username=data['email'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
            )
            
            patient = Patient.objects.create(
                user=user,
                date_of_birth=data['date_of_birth'],
                height=data['height'],
                weight=data['weight'],
                insurance=data['insurance'],
                sex=data['sex'],
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
            patient.save()  # This will also calculate and save BMI

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