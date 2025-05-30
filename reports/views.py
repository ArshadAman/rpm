from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Reports, Documentation
from rpm_users.models import Patient, Moderator
from .serializers import ReportSerializer
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .forms import DocumentationForm  # Ensure you have a Django form for validation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import date
from django.forms.models import model_to_dict

# from rpm.customPermission import CustomSSOAuthentication

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_your_reports(request, patient_id):
    email = request.email
    if patient := Patient.objects.filter(email=email).first():
        try:
            reports = Reports.objects.filter(Q(patient=patient)).order_by("-created_at")
            serializer = ReportSerializer(reports, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Reports.DoesNotExist:
            return Response(
                {"error": "Reports not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    return Response({"error": "Patient not exists"}, status=status.HTTP_404_NOT_FOUND)

@login_required
def get_patients_reports(request):
    email = request.user.email
    if moderator := Moderator.objects.filter(email=email).first():
        try:
            reports = Reports.objects.filter(
                patient__moderator_assigned=moderator
            ).order_by("-created_at")
            serializer = ReportSerializer(reports, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Reports.DoesNotExist:
            return Response(
                {"error": "Reports not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    return Response({"error": "Moderator not exists"}, status=status.HTTP_404_NOT_FOUND)

@login_required
def get_single_report(request, report_id):
    user = request.user  # Get the logged-in user
    print(f"DEBUG: Logged-in User = {user}")

    try:
        report = Reports.objects.get(id=report_id)
        print(f"DEBUG: Report Found - ID: {report.id}")

        # Allow access if the user is a moderator or the assigned patient
        if Moderator.objects.filter(user=user).exists() or user == report.patient.user:
            print("DEBUG: Access granted")

            # Fetch related documentations
            documentations = report.documentations.all()

            context = {
                "report": report,
                "documentations": documentations,
            }

            return render(request, "index.html", context)

        print("DEBUG: Access denied - Only authorized users can view this report")
        return render(request, "errors/403.html", {"error": "You are not authorized to view this report"}, status=403)

    except Reports.DoesNotExist:
        print("DEBUG: Report not found")
        return render(request, "errors/404.html", {"error": "Report not found"}, status=404)


@login_required
def get_all_reports(request, patient_id):
    user = request.user  # Get the logged-in user
    print(f"DEBUG: Logged-in User = {user}")

    # Check if user is a Moderator
    is_moderator = Moderator.objects.filter(user=user).exists()

    # Fetch reports - If user is a moderator, fetch all reports, else fetch only the patient's reports
    patient = Patient.objects.filter(id=patient_id).first()
    print(f"DEBUG: Patient = {patient}")
    
    if not patient:
        print("DEBUG: Patient not found")
        return JsonResponse({"error": "Patient not found"}, status=404)
    
    # Check if the logged-in user is the patient or a moderator
    is_patient = Patient.objects.filter(user=user, id=patient_id).exists()
    
    if is_moderator or is_patient:
        reports = Reports.objects.filter(patient=patient).order_by("-created_at")
        print("reports", reports)
    else:
        print(f"DEBUG: User {user} is not authorized to view reports for patient {patient_id}")
        return JsonResponse({"error": "Not authorized to view these reports"}, status=403)

    # Return empty reports array if no reports exist
    if not reports.exists():
        print("DEBUG: No reports found, returning empty array")
        return JsonResponse({"reports": []}, safe=False)

    # Prepare JSON response with all fields
    data = {
        "reports": [
            {**model_to_dict(report), "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S")} for report in reports
        ]
    }

    return JsonResponse(data, safe=False)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_report(request):
    email = request.email
    if patient := Patient.objects.filter(email=email).first():
        data = request.data

        # List all model fields you want to accept
        report_fields = {
            "blood_pressure": data.get("blood_pressure", ""),
            "heart_rate": data.get("heart_rate", ""),
            "spo2": data.get("spo2", ""),
            "temperature": data.get("temperature", ""),
            "symptoms": data.get("symptoms", ""),
            "device_id": data.get("device_id", ""),
            "created_at_device": data.get("created_at_device", ""),
            "data_type": data.get("data_type", ""),
            "imei": data.get("imei", ""),
            "iccid": data.get("iccid", ""),
            "serial_number": data.get("serial_number", ""),
            "model_number": data.get("model_number", ""),
            "is_test": data.get("is_test", ""),
            "user_id": data.get("user_id", ""),
            "systolic_blood_pressure": data.get("systolic_blood_pressure", ""),
            "diastolic_blood_pressure": data.get("diastolic_blood_pressure", ""),
            "pulse": data.get("pulse", ""),
            "irregular_heartbeat": data.get("irregular_heartbeat", ""),
            "hand_shaking": data.get("hand_shaking", ""),
            "triple_mode": data.get("triple_mode", ""),
            "battery_level": data.get("battery_level", ""),
            "signal_strength": data.get("signal_strength", ""),
            "measurement_timestamp": data.get("measurement_timestamp", ""),
            "timezone": data.get("timezone", ""),
            "blood_glucose": data.get("blood_glucose", ""),
            "glucose_unit": data.get("glucose_unit", ""),
            "test_paper_type": data.get("test_paper_type", ""),
            "sample_type": data.get("sample_type", ""),
            "meal_mark": data.get("meal_mark", ""),
            "signal_level": data.get("signal_level", ""),
            "measurement_timezone": data.get("measurement_timezone", ""),
            "upload_timestamp": data.get("upload_timestamp", ""),
            "upload_timezone": data.get("upload_timezone", ""),
        }

        report = Reports.objects.create(patient=patient, **report_fields)
        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"error": "Patient not exists"}, status=status.HTTP_404_NOT_FOUND)
@login_required
def add_documentation(request, patient_id):
    user = request.user
    print(user)
    # Check if the user is a moderator
    if not Moderator.objects.filter(user=user).exists():
        return render(request, "errors/403.html", {"error": "Only moderators can add documentation"}, status=403)

    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get the latest three reports for this patient if they exist
    latest_reports = Reports.objects.filter(patient=patient).order_by('-created_at')[:3]
    
    if request.method == "POST":
        form = DocumentationForm(request.POST, request.FILES)
        if form.is_valid():
            documentation = form.save(commit=False)
            documentation.patient = patient
            # Add the moderator who wrote the documentation
            documentation.written_by = user
            # Only associate with report if it exists
            if latest_reports:
                documentation.report = latest_reports[0]
            documentation.save()
            return redirect(f"/view-patient/{patient_id}/?action=access")  # Redirect to patient's view page
    else:
        form = DocumentationForm()

    context = {
        "form": form, 
        "patient": patient,
        "reports": latest_reports
    }
    
    return render(request, "reports/add_docs.html", context)


@csrf_exempt
def data_from_mio_connect(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        # Parse JSON data
        try:
            body = json.loads(request.body)
            print(f"Received data from MioConnect: {json.dumps(body)}")
        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid JSON data: {str(e)}"}, status=400)

        data = body.get('data', {})
        device_serial = data.get('sn', '')
        if not device_serial:
            return JsonResponse({"error": "Missing device serial number"}, status=400)

        patient = Patient.objects.filter(device_serial_number=device_serial).first()
        if not patient:
            return JsonResponse({"error": f"No patient found with device serial number: {device_serial}"}, status=404)

        # List all possible fields from both device types
        report_fields = {
            # Common
            'device_id': body.get('deviceId', ''),
            'created_at_device': str(body.get('createdAt', '')),
            'data_type': data.get('data_type', ''),
            'imei': data.get('imei', ''),
            'iccid': data.get('iccid', ''),
            'serial_number': data.get('sn', ''),
            'model_number': body.get('modelNumber', ''),
            'is_test': str(body.get('isTest', '')),
            # Sphygmomanometer
            'user_id': str(data.get('user', '')),
            'systolic_blood_pressure': str(data.get('sys', '')),
            'diastolic_blood_pressure': str(data.get('dia', '')),
            'pulse': str(data.get('pul', '')),
            'irregular_heartbeat': str(data.get('ihb', '')),
            'hand_shaking': str(data.get('hand', '')),
            'triple_mode': str(data.get('tri', '')),
            'battery_level': str(data.get('bat', '')),
            'signal_strength': str(data.get('sig', '')),
            'measurement_timestamp': str(data.get('ts', '')),
            'timezone': str(data.get('tz', '')),
            # Blood Glucose Meter
            'blood_glucose': str(data.get('data', '')),
            'glucose_unit': str(data.get('unit', '')),
            'test_paper_type': str(data.get('sample', '')),
            'sample_type': str(data.get('target', '')),
            'meal_mark': str(data.get('meal', '')),
            'signal_level': str(data.get('sig_lvl', '')),
            'measurement_timezone': str(data.get('ts_tz', '')),
            'upload_timestamp': str(data.get('uptime', '')),
            'upload_timezone': str(data.get('uptime_tz', '')),
        }

        # For compatibility, also fill old fields if possible
        if report_fields['systolic_blood_pressure'] and report_fields['diastolic_blood_pressure']:
            report_fields['blood_pressure'] = f"{report_fields['systolic_blood_pressure']}/{report_fields['diastolic_blood_pressure']}"
        else:
            report_fields['blood_pressure'] = ''
        report_fields['heart_rate'] = report_fields['pulse']
        report_fields['spo2'] = ''
        report_fields['temperature'] = ''
        report_fields['symptoms'] = ''

        report = Reports.objects.create(patient=patient, **report_fields)
        return JsonResponse({
            "success": True,
            "received_data": body,
            "saved_report_id": report.id,
            "patient_id": patient.id
        })
    except Exception as err:
        print(f"Unexpected error: {str(err)}")
        return JsonResponse({"error": "An unexpected error occurred while processing the request"}, status=500)


@login_required
def view_documentation(request):
    # Check if the user is a moderator
    if not Moderator.objects.filter(user=request.user).exists():
        return render(request, "errors/403.html", {"error": "Only moderators can view documentation"}, status=403)
    
    # Get the date filter from the request
    date = request.GET.get('date')
    
    # Get all documentation for the moderator's patients
    moderator = Moderator.objects.get(user=request.user)
    patient_ids = Patient.objects.filter(moderator_assigned=moderator).values_list("id", flat=True)
    
    # Apply date filter if provided
    if date:
        documentations = Documentation.objects.filter(
            patient__in=patient_ids,
            created_at__date=date
        ).select_related('patient').order_by('-created_at')
    else:
        documentations = Documentation.objects.filter(
            patient__in=patient_ids
        ).select_related('patient').order_by('-created_at')
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        # For AJAX requests, return only the documentation cards
        return render(request, "reports/documentation_cards.html", {
            'documentations': documentations
        })
    else:
        # For regular requests, return the full page
        return render(request, "reports/view_documentation.html", {
            'documentations': documentations
        })

@login_required
def edit_patient(request, patient_id):
    user = request.user
    
    # Check if the user is a moderator or the patient themselves
    is_moderator = Moderator.objects.filter(user=user).exists()
    is_patient = Patient.objects.filter(user=user, id=patient_id).exists()
    
    if not is_moderator and not is_patient:
        return render(request, "errors/403.html", {"error": "You are not authorized to edit this patient information"}, status=403)
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == "POST":
        try:
            # Update user information
            patient.user.first_name = request.POST.get('first_name')
            patient.user.last_name = request.POST.get('last_name')
            patient.user.save()
            
            # Update patient information
            date_of_birth_str = request.POST.get('date_of_birth')
            if date_of_birth_str:
                # Convert string to date object
                from datetime import datetime
                patient.date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            
            patient.sex = request.POST.get('sex')
            patient.weight = request.POST.get('weight')
            patient.height = request.POST.get('height')
            patient.insurance = request.POST.get('insurance')
            patient.monitoring_parameters = request.POST.get('monitoring_parameters')
            patient.device_serial_number = request.POST.get('device_serial_number')
            patient.drink = request.POST.get('drink')
            patient.smoke = request.POST.get('smoke')
            patient.allergies = request.POST.get('allergies')
            
            # Recalculate BMI
            if patient.weight and patient.height:
                height_in_meters = float(patient.height) / 100
                patient.bmi = round(float(patient.weight) / (height_in_meters ** 2), 2)
            
            # No need to manually calculate age - it's handled by the property in the model
            
            patient.save()
            
            return JsonResponse({
                'success': True,
                'patient_id': patient.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # GET request - display the edit form
    return render(request, "reports/edit_patient.html", {
        'patient': patient
    })