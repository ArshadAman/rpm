from django.contrib import admin
from .models import Moderator, Patient
# Register your models here.
admin.site.register([Moderator, Patient])