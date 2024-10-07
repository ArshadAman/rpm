from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests

from reports.models import Reports
from reports.serializers import ReportSerializer
from .models import Patient, Moderator
from .serializers import PatientSerializer, ModeratorSerializer


@api_view(["POST"])
def create_patient(request):
    # check if the patient is already in the sso, and if the patient is in the sso, then check if the patient is already in the database and if the user in the database then return the patient object and if the user is not in the database then create new patient object, and if the user is not in sso then create the user in the sso and also in the database

    data = request.data
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    entered_otp = data.get("entered_otp")
    phone_number = data.get("phone_number")

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
        patient = Patient.objects.filter(email=email).first()
        if patient:
            return Response(
                {"message": "User already exists"}, status=status.HTTP_409_CONFLICT
            )
        else:
            # create new patient object
            patient = Patient.objects.create(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                entered_otp=entered_otp,
                phone_number=phone_number,
            )
            return Response(
                {"message": "Patient successfully created"},
                status=status.HTTP_201_CREATED,
            )


@api_view(["POST"])
def create_moderator(request):
    # check if the moderator is already in the sso, and if the moderator is in the sso, then check if the moderator is already in the database and if the user in the database then return the moderator object and if the user is not in the database then create new moderator object, and if the user is not in sso then create the user in the sso
    data = request.data
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    entered_otp = data.get("entered_otp")
    phone_number = data.get("phone_number")

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
        patient = Moderator.objects.filter(email=email).first()
        if patient:
            return Response(
                {"message": "User already exists"}, status=status.HTTP_409_CONFLICT
            )
        else:
            # create new patient object
            patient = Moderator.objects.create(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                entered_otp=entered_otp,
                phone_number=phone_number,
            )
            return Response(
                {"message": "Patient successfully created"},
                status=status.HTTP_201_CREATED,
            )

@api_view(['POST'])            
def assign_patient(request, patient_id, moderator_id):
    patient = Patient.objects.get(id=patient)
    moderator = Moderator.objects.get(id=moderator_id)
    patient.moderator_assigned = moderator
    patient.save()
    
@api_view(['POST'])
def moderator_actions(request, patient_id, action):
    # So the moderator assigned will be something like the moderator can access the patient details, update the patient data
    # get the moderator
    email - request.email
    moderator = Moderator.objects.get(email=email)
    patient = Patient.objects.get(id=patient_id)
     
    if action == 'access'.lower():
        # access patient details
        serializer = PatientSerializer(patient)
        return Response(serializer.data)
    
    elif action == 'update'.lower():
        # update patient data
        serializer = PatientSerializer(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif action == 'delete':
        # delete patient
        patient.delete()
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
    
    elif action == 'update-report':
        # update patient's report
        report_id = request.data.get('report_id')
        report = Reports.objects.get(id=report_id)
        if not report.patient == patient:
            return Response({"error": "This report does not belong to this patient."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReportSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif action == 'delete-report':
        # delete patient's report
        report_id = request.data.get('report_id')
        report = Reports.objects.get(id=report_id)
        if not report.patient == patient:
            return Response({"error": "This report does not belong to this patient."}, status=status.HTTP_400_BAD_REQUEST)
        report.delete()
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
    
def all_moderators(request):
    moderators = Moderator.objects.all()
    serializer = ModeratorSerializer(moderators, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_patient(request, patient_id):
    pass