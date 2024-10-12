from rest_framework.serializers import ModelSerializer
from .models import Patient, Moderator
from reports.models import Reports
from reports.serializers import ReportSerializer
from django.contrib.auth.models import User

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class ModeratorSerializer(ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Moderator
        fields = '__all__'

class PatientSerializer(ModelSerializer):
    moderator_assigned = ModeratorSerializer()
    user = UserSerializer()
    reports = ReportSerializer(many=True)
    class Meta:
        model = Patient
        fields = '__all__'