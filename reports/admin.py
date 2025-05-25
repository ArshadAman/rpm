from django.contrib import admin
from .models import Reports, Documentation

admin.site.register([Reports, Documentation])
