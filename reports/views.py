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

            return render(request, "reports/report.html", context)

        print("DEBUG: Access denied - Only authorized users can view this report")
        return render(request, "errors/403.html", {"error": "You are not authorized to view this report"}, status=403)

    except Reports.DoesNotExist:
        print("DEBUG: Report not found")
        return render(request, "errors/404.html", {"error": "Report not found"}, status=404)

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
