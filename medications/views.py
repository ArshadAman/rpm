from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
import json
from datetime import timedelta

from .gemini_service import GeminiMedicineService
from .models import (
    Medicine, Disease, PatientMedicineHistory, 
    MedicineSearchCache, DiseaseMedicine, MedicineInteraction
)
from rpm_users.models import Patient

@login_required
@require_http_methods(["POST"])
def search_medicines_by_disease(request):
    """
    Search for medicines with intelligent caching
    """
    try:
        data = json.loads(request.body)
        disease = data.get('disease', '').strip()
        force_refresh = data.get('force_refresh', False)
        
        if not disease:
            return JsonResponse({
                'success': False,
                'error': 'Disease name is required'
            })
        
        # Initialize Gemini service
        gemini_service = GeminiMedicineService()
        
        # Search for medicines (with caching)
        result = gemini_service.search_medicines_for_disease(disease, force_refresh)
        
        return JsonResponse(result)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def check_drug_interactions(request):
    """
    Check drug interactions using cached data first
    """
    try:
        data = json.loads(request.body)
        medicine_name = data.get('medicine_name', '').strip()
        patient_id = data.get('patient_id')
        
        if not medicine_name or not patient_id:
            return JsonResponse({
                'success': False,
                'error': 'Medicine name and patient ID are required'
            })
        
        # Get patient's current medications
        try:
            patient = Patient.objects.get(id=patient_id)
            current_medications = []
            
            if patient.medications:
                current_medications = [med.strip() for med in patient.medications.split('\n') if med.strip()]
        
        except Patient.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Patient not found'
            })
        
        # Log this search
        medicine_obj = Medicine.objects.filter(name__iexact=medicine_name).first()
        if medicine_obj:
            PatientMedicineHistory.objects.create(
                patient=patient,
                medicine=medicine_obj,
                search_query=medicine_name,
                viewed_by=request.user,
                interaction_checked=True
            )
        
        # Initialize Gemini service
        gemini_service = GeminiMedicineService()
        
        # Check interactions (with caching)
        result = gemini_service.get_drug_interactions_from_cache(medicine_name, current_medications)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_cached_medicines(request):
    """Get all cached medicines for admin/debugging"""
    medicines = Medicine.objects.all().order_by('-search_count', 'name')[:50]
    
    data = []
    for med in medicines:
        data.append({
            'name': med.name,
            'generic_name': med.generic_name,
            'drug_class': med.drug_class,
            'search_count': med.search_count,
            'last_searched': med.last_searched.isoformat() if med.last_searched else None,
            'fda_approved': med.fda_approved,
            'created_at': med.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'medicines': data,
        'total': Medicine.objects.count()
    })

@login_required
@require_http_methods(["POST"])
def refresh_medicine_cache(request):
    """Force refresh medicine data from AI"""
    try:
        data = json.loads(request.body)
        disease = data.get('disease', '').strip()
        
        if not disease:
            return JsonResponse({
                'success': False,
                'error': 'Disease name is required'
            })
        
        gemini_service = GeminiMedicineService()
        result = gemini_service.search_medicines_for_disease(disease, force_refresh=True)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_diseases_list(request):
    """Get list of all diseases for autocomplete"""
    query = request.GET.get('q', '').strip()
    
    diseases = Disease.objects.all()
    
    if query:
        diseases = diseases.filter(
            Q(name__icontains=query) |
            Q(normalized_name__icontains=query)
        )
    
    diseases = diseases.order_by('name')[:20]  # Limit to 20 results
    
    data = [{'id': d.id, 'name': d.name} for d in diseases]
    
    return JsonResponse({
        'success': True,
        'diseases': data
    })

@login_required
def get_medicine_detail(request, medicine_id):
    """Get detailed information about a specific medicine"""
    try:
        medicine = get_object_or_404(Medicine, id=medicine_id)
        
        # Track view
        medicine.increment_search_count()
        
        # Get related diseases
        related_diseases = [dm.disease.name for dm in medicine.disease_indications.all()]
        
        # Get interactions count
        interactions_count = MedicineInteraction.objects.filter(
            Q(medicine_a=medicine) | Q(medicine_b=medicine)
        ).count()
        
        data = {
            'id': medicine.id,
            'name': medicine.name,
            'generic_name': medicine.generic_name,
            'brand_names': medicine.brand_names,
            'drug_class': medicine.drug_class,
            'mechanism': medicine.mechanism,
            'dosage': medicine.dosage,
            'administration': medicine.administration,
            'side_effects': medicine.side_effects,
            'contraindications': medicine.contraindications,
            'drug_interactions': medicine.drug_interactions,
            'monitoring': medicine.monitoring,
            'fda_approved': medicine.fda_approved,
            'pregnancy_category': medicine.pregnancy_category,
            'search_count': medicine.search_count,
            'last_searched': medicine.last_searched.isoformat() if medicine.last_searched else None,
            'related_diseases': related_diseases,
            'interactions_count': interactions_count,
            'last_updated': medicine.last_updated_from_ai.isoformat(),
            'is_stale': medicine.is_stale()
        }
        
        return JsonResponse({
            'success': True,
            'medicine': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_popular_searches(request):
    """Get most popular medicine searches"""
    try:
        limit = int(request.GET.get('limit', 10))
        
        # Popular medicines
        popular_medicines = Medicine.objects.filter(
            search_count__gt=0
        ).order_by('-search_count', '-last_searched')[:limit]
        
        # Popular disease searches
        popular_caches = MedicineSearchCache.objects.filter(
            access_count__gt=0
        ).order_by('-access_count', '-last_accessed')[:limit]
        
        medicines_data = []
        for med in popular_medicines:
            medicines_data.append({
                'name': med.name,
                'generic_name': med.generic_name,
                'search_count': med.search_count,
                'last_searched': med.last_searched.isoformat() if med.last_searched else None
            })
        
        searches_data = []
        for cache in popular_caches:
            searches_data.append({
                'query': cache.search_query,
                'access_count': cache.access_count,
                'results_count': cache.total_results,
                'last_accessed': cache.last_accessed.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'popular_medicines': medicines_data,
            'popular_searches': searches_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_patient_medicine_history(request, patient_id):
    """Get medicine search history for a specific patient"""
    try:
        patient = get_object_or_404(Patient, id=patient_id)
        
        history = PatientMedicineHistory.objects.filter(
            patient=patient
        ).select_related('medicine', 'disease_context', 'viewed_by').order_by('-created_at')
        
        page = request.GET.get('page', 1)
        paginator = Paginator(history, 20)
        history_page = paginator.get_page(page)
        
        data = []
        for entry in history_page:
            data.append({
                'id': entry.id,
                'medicine_name': entry.medicine.name,
                'medicine_generic': entry.medicine.generic_name,
                'disease_context': entry.disease_context.name if entry.disease_context else None,
                'search_query': entry.search_query,
                'interaction_checked': entry.interaction_checked,
                'viewed_by': entry.viewed_by.get_full_name() if entry.viewed_by else None,
                'created_at': entry.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'history': data,
            'total_pages': paginator.num_pages,
            'current_page': history_page.number,
            'total_count': paginator.count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def log_medicine_view(request):
    """Log when a user views a medicine (for analytics)"""
    try:
        data = json.loads(request.body)
        medicine_id = data.get('medicine_id')
        patient_id = data.get('patient_id')
        disease_context = data.get('disease_context')
        
        if not medicine_id:
            return JsonResponse({
                'success': False,
                'error': 'Medicine ID is required'
            })
        
        medicine = get_object_or_404(Medicine, id=medicine_id)
        patient = None
        disease = None
        
        if patient_id:
            patient = get_object_or_404(Patient, id=patient_id)
        
        if disease_context:
            disease = Disease.objects.filter(name__iexact=disease_context).first()
        
        # Create history entry
        if patient:
            PatientMedicineHistory.objects.create(
                patient=patient,
                medicine=medicine,
                disease_context=disease,
                viewed_by=request.user
            )
        
        # Update medicine search count
        medicine.increment_search_count()
        
        return JsonResponse({
            'success': True,
            'message': 'View logged successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_search_analytics(request):
    """Get analytics data for medicine searches"""
    try:
        # Date range filter
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Total searches
        total_searches = MedicineSearchCache.objects.filter(
            created_at__gte=start_date
        ).aggregate(
            total_count=Count('id'),
            total_access=Count('access_count')
        )
        
        # Most searched diseases
        top_diseases = MedicineSearchCache.objects.filter(
            created_at__gte=start_date
        ).order_by('-access_count')[:10]
        
        # Most viewed medicines
        top_medicines = Medicine.objects.filter(
            last_searched__gte=start_date
        ).order_by('-search_count')[:10]
        
        # Cache hit rate
        cache_stats = MedicineSearchCache.objects.filter(
            created_at__gte=start_date
        ).aggregate(
            total_caches=Count('id'),
            total_accesses=Count('access_count')
        )
        
        diseases_data = []
        for cache in top_diseases:
            diseases_data.append({
                'disease': cache.search_query,
                'search_count': cache.access_count,
                'results_count': cache.total_results,
                'last_searched': cache.last_accessed.isoformat()
            })
        
        medicines_data = []
        for med in top_medicines:
            medicines_data.append({
                'name': med.name,
                'generic_name': med.generic_name,
                'search_count': med.search_count,
                'last_searched': med.last_searched.isoformat() if med.last_searched else None
            })
        
        return JsonResponse({
            'success': True,
            'analytics': {
                'date_range': f"Last {days} days",
                'total_searches': total_searches['total_count'] or 0,
                'total_accesses': total_searches['total_access'] or 0,
                'top_diseases': diseases_data,
                'top_medicines': medicines_data,
                'cache_stats': cache_stats
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_cache_analytics(request):
    """Get cache performance analytics"""
    try:
        # Cache statistics
        total_medicines = Medicine.objects.count()
        total_diseases = Disease.objects.count()
        total_caches = MedicineSearchCache.objects.count()
        
        # Stale data
        stale_medicines = Medicine.objects.filter(
            last_updated_from_ai__lt=timezone.now() - timedelta(days=30)
        ).count()
        
        # Most accessed caches
        popular_caches = MedicineSearchCache.objects.order_by('-access_count')[:10]
        
        # Recent AI calls
        recent_ai_calls = Medicine.objects.filter(
            last_updated_from_ai__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        cache_data = []
        for cache in popular_caches:
            cache_data.append({
                'query': cache.search_query,
                'access_count': cache.access_count,
                'results_count': cache.total_results,
                'created_at': cache.created_at.isoformat(),
                'is_stale': cache.is_stale()
            })
        
        return JsonResponse({
            'success': True,
            'cache_analytics': {
                'total_medicines': total_medicines,
                'total_diseases': total_diseases,
                'total_caches': total_caches,
                'stale_medicines': stale_medicines,
                'recent_ai_calls': recent_ai_calls,
                'cache_hit_rate': f"{((total_caches / max(total_medicines, 1)) * 100):.1f}%",
                'popular_caches': cache_data
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
