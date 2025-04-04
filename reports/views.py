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

from rpm.customPermission import CustomSSOAuthentication

@api_view(["GET"])
@permission_classes([CustomSSOAuthentication])
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
    if is_moderator:
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            print("DEBUG: Patient not found")
            return JsonResponse({"error": "Patient not found"}, status=404)
        reports = Reports.objects.filter(patient=patient).order_by("-created_at")
    else:
        return JsonResponse({"error": "Not a moderator"}, status=404)

    if not reports.exists():
        print("DEBUG: No reports found")
        return JsonResponse({"error": "No reports found"}, status=404)

    # Prepare JSON response
    data = {
        "reports": [
            {
                "patient_name": report.patient.user.first_name,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "heart_rate": report.heart_rate,
                "blood_pressure": report.blood_pressure,
                "temperature": report.temperature,
                "documentations": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "file_url": doc.file.url if doc.file else None,
                    }
                    for doc in report.documentations.all()
                ],
            }
            for report in reports
        ]
    }

    return JsonResponse(data, safe=False)

@api_view(["POST"])
@permission_classes([CustomSSOAuthentication])
def create_report(request):
    email = request.email
    if patient := Patient.objects.filter(email=email).first():
        data = request.data
        blood_pressure = data.get("blood_pressure")
        heart_rate = data.get("heart_rate")
        spo2 = data.get("spo2")
        temperature = data.get("temperature")
        symptoms = data.get("symptoms")
        report = Reports.objects.create(
            patient=patient,
            blood_pressure=blood_pressure,
            heartbeat_rate=heart_rate,
            spo2=spo2,
            temperature=temperature,
            symptoms=symptoms,
        )
        serializer = ReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"error": "Patient not exists"}, status=status.HTTP_404_NOT_FOUND)

@login_required
def add_documentation(request, report_id):
    user = request.user

    # Check if the user is a moderator
    if not Moderator.objects.filter(user=user).exists():
        return render(request, "errors/403.html", {"error": "Only moderators can add documentation"}, status=403)

    report = get_object_or_404(Reports, id=report_id)

    if request.method == "POST":
        form = DocumentationForm(request.POST, request.FILES)
        if form.is_valid():
            documentation = form.save(commit=False)
            documentation.report = report
            documentation.save()
            return redirect("get_single_report", report_id=report.id)  # Redirect to the report view after adding

    else:
        form = DocumentationForm()

    return render(request, "reports/add_docs.html", {"form": form, "report": report})


@csrf_exempt
def data_from_mio_connect(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        body = json.loads(request.body)
        print(f"Received data from MioConnect: {json.dumps(body)}")
        result = {
            "success": True,
            "received_data": body  # Include the received body in the response
        }
        return JsonResponse(result)
    except Exception as err:
        print(err)
        return JsonResponse({"error": str(err)}, status=400)
