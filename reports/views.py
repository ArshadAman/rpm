from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Reports
from rpm_users.models import Patient, Moderator
from .serializers import ReportSerializer
from django.db.models import Q
# Create your views here.


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_reports(request, patient_id):
    email = request.email
    if patient:= Patient.objects.filter(email = email).first():
        pass  # Additional validation for patient access
    elif moderator:= Moderator.objects.filter(email = email).first():
        pass
    try:
        reports = Reports.objects.filter(Q(patient=patient)).order_by('-created_at')
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Reports.DoesNotExist:
        return Response(
            {"error": "Reports not found"},
            status=status.HTTP_404_NOT_FOUND,
        )