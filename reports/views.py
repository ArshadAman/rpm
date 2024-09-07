from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Reports
from rpm_users.models import Patient, Moderator
from .serializers import ReportSerializer
from django.db.models import Q

# Create your views here.


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_patients_reports(request):
    email = request.email
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

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_single_report(request, report_id):
    email = request.email
    if moderator := Moderator.objects.filter(email=email).first():
        try:
            report = Reports.objects.get(
                id = report_id
            )
            if report.patient__moderator_assigned == moderator:
                serializer = ReportSerializer(report)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "You are not authorized to view this report"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Reports.DoesNotExist:
            return Response(
                {"error": "Reports not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    return Response({"error": "Moderator not exists"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
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
