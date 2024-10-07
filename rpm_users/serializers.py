from rest_framework.serializers import ModelSerializer
from .models import Patient, Moderator
from reports.models import Reports
from reports.serializers import ReportSerializer

class ModeratorSerializer(ModelSerializer):
    class Meta:
        model = Moderator
        fields = '__all__'

class PatientSerializer(ModelSerializer):
    moderator_assigned = ModelSerializer()
    reports = ReportSerializer(many=True)
    class Meta:
        model = Patient
        fields = '__all__'