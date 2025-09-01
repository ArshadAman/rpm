from django.contrib import admin
from .models import Disease, Medicine, DiseaseMedicine, MedicineSearchCache, MedicineInteraction

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'normalized_name', 'created_at']
    search_fields = ['name', 'normalized_name']

@admin.register(Medicine)  
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'generic_name', 'drug_class', 'fda_approved', 'search_count', 'last_searched']
    list_filter = ['fda_approved', 'drug_class', 'created_at']
    search_fields = ['name', 'generic_name', 'brand_names']
    readonly_fields = ['search_count', 'last_searched', 'created_at', 'updated_at']

@admin.register(MedicineSearchCache)
class MedicineSearchCacheAdmin(admin.ModelAdmin):
    list_display = ['search_query', 'total_results', 'access_count', 'created_at', 'last_accessed']
    readonly_fields = ['access_count', 'created_at', 'last_accessed']