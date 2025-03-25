from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Reports
from rpm_users.models import Patient, Moderator
from .serializers import ReportSerializer
from django.db.models import Q

from rpm.customPermission import CustomSSOAuthentication
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
# Create your views here.

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

@api_view(["GET"])
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

        # Allow access only if the user is a moderator
        if Moderator.objects.filter(user=user).exists():
            print("DEBUG: Access granted (Moderator)")
            report_data = {
                "id": report.id,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": report.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "patient": {
                    "id": report.patient.id,
                    "name": f"{report.patient.user.first_name} {report.patient.user.last_name}",
                    "email": report.patient.user.email,
                },
                "blood_pressure": report.blood_pressure,
                "heartbeat_rate": report.heart_rate,
                "spo2": report.spo2,
                "temperature": report.temperature,
                "symptoms": report.symptoms,
            }
            print(report_data)
            return JsonResponse({"report": report_data}, status=200)

        print("DEBUG: Access denied - Only moderators can access this report")
        return JsonResponse({"error": "Only moderators can view this report"}, status=403)

    except Reports.DoesNotExist:
        print("DEBUG: Report not found")
        return JsonResponse({"error": "Report not found"}, status=404)

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
