from rest_framework.serializers import ModelSerializer
from .models import Reports
from rpm_users.models import Patient, Moderator

class ReportSerializer(ModelSerializer):
    class Meta:
        model = Reports
        fields = '__all__'