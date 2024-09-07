from rest_framework.serializers import ModelSerializer
from .models import Patient, Moderator
from reports.models import Reports

class ModeratorSerializer(ModelSerializer):
    class Meta:
        model = Moderator
        fields = '__all__'

class PatientSerializer(ModelSerializer):
    moderator_assigned = ModelSerializer(many=True)
    class Meta:
        model = Patient
        fields = '__all__'