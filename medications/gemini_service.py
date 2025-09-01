import google.generativeai as genai
import json
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from typing import Dict, List, Any
import logging
import time
from fuzzywuzzy import fuzz
from .models import (
    Disease, Medicine, DiseaseMedicine, MedicineSearchCache, 
    CachedMedicineResult, MedicineInteraction, PatientMedicineHistory
)
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class GeminiMedicineService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Updated to use Gemini 1.5 Flash model (latest)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Configure generation settings for better reliability
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        # Setup retry strategy for network errors
        self.setup_retry_session()
    
    def setup_retry_session(self):
        """Setup requests session with retry strategy"""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def search_medicines_for_disease(self, disease_query: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Search for medicines with intelligent caching and improved error handling
        """
        # Normalize query
        normalized_query = disease_query.lower().strip()
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_result = self._get_cached_result(normalized_query)
            if cached_result:
                logger.info(f"Returning cached result for: {disease_query}")
                return cached_result
        
        # Check if we have this disease in our database
        disease_obj = self._get_or_create_disease(disease_query)
        
        # Get existing medicines for this disease
        existing_medicines = self._get_existing_medicines_for_disease(disease_obj)
        
        # If we have recent, comprehensive data, return it
        if existing_medicines and not force_refresh:
            recent_medicines = [m for m in existing_medicines if not m.is_stale()]
            if len(recent_medicines) >= 3:  # Minimum threshold
                logger.info(f"Returning existing medicines for: {disease_query}")
                return self._format_cached_medicines(disease_obj, recent_medicines)
        
        # Fetch from Gemini AI with retry logic
        logger.info(f"Fetching from Gemini AI for: {disease_query}")
        ai_result = self._fetch_from_gemini_with_retry(disease_query)
        
        if ai_result['success']:
            # Save to database
            saved_medicines = self._save_medicines_to_db(disease_obj, ai_result['data'])
            
            # Create cache entry
            self._create_cache_entry(normalized_query, saved_medicines, ai_result)
            
            return ai_result
        
        # Fallback to existing data if AI fails
        if existing_medicines:
            logger.warning(f"AI failed, returning existing data for: {disease_query}")
            return self._format_cached_medicines(disease_obj, existing_medicines)
        
        return ai_result
    
    def _fetch_from_gemini_with_retry(self, disease: str, max_retries: int = 3) -> Dict[str, Any]:
        """Fetch medicine data from Gemini AI with retry logic"""
        
        prompt = f"""
        As a medical AI assistant, provide information about medicines commonly used to treat {disease}.
        
        Please return a JSON response with the following structure:
        {{
            "disease": "{disease}",
            "medicines": [
                {{
                    "name": "Medicine Name",
                    "generic_name": "Generic Name",
                    "brand_names": ["Brand1", "Brand2"],
                    "drug_class": "Drug Classification",
                    "mechanism": "How it works",
                    "dosage": "Typical dosage information",
                    "administration": "How to take it",
                    "side_effects": [
                        "Common side effect 1",
                        "Common side effect 2"
                    ],
                    "contraindications": [
                        "When not to use",
                        "Medical conditions to avoid"
                    ],
                    "monitoring": "What to monitor while on this medication",
                    "fda_approved": true/false,
                    "pregnancy_category": "Category if applicable",
                    "drug_interactions": [
                        "Drug interaction 1",
                        "Drug interaction 2"
                    ],
                    "indication": "Specific indication for this disease",
                    "is_first_line": true/false
                }}
            ],
            "disclaimer": "This information is for educational purposes only. Always consult with a healthcare provider."
        }}
        
        Focus on the most commonly prescribed and FDA-approved medications. Include at least 5-7 medicines if available.
        Be accurate and include real medical information from FDA guidelines.
        Return only valid JSON without any markdown formatting.
        """
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Use the configured generation settings
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config
                )
                
                processing_time = time.time() - start_time
                
                # Check if response is blocked
                if response.candidates and response.candidates[0].finish_reason.name == "SAFETY":
                    logger.warning(f"Response blocked by safety filters for disease: {disease}")
                    return {
                        'success': False,
                        'error': 'Content blocked by safety filters. Please try a different search term.',
                        'attempt': attempt + 1
                    }
                
                # Clean up the response text
                response_text = response.text.strip()
                
                # Remove markdown formatting if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                
                # Parse JSON response
                medicine_data = json.loads(response_text.strip())
                
                logger.info(f"Successfully fetched data for {disease} on attempt {attempt + 1}")
                
                return {
                    'success': True,
                    'data': medicine_data,
                    'processing_time': processing_time,
                    'raw_response': response.text,
                    'attempt': attempt + 1,
                    'model_used': 'gemini-1.5-flash'
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for disease '{disease}' on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': 'Failed to parse medicine information after multiple attempts',
                        'raw_response': response.text if 'response' in locals() else None,
                        'attempts': max_retries
                    }
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Gemini API error for disease '{disease}' on attempt {attempt + 1}: {error_msg}")
                
                # Check for specific network errors
                if any(net_error in error_msg.lower() for net_error in ['network', 'connection', 'timeout', 'unreachable']):
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"Network error detected, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                
                # Check for rate limiting
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = 5 * (attempt + 1)
                        logger.info(f"Rate limit detected, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': f'Network error after {max_retries} attempts: {error_msg}',
                        'attempts': max_retries
                    }
        
        return {
            'success': False,
            'error': f'Failed after {max_retries} attempts',
            'attempts': max_retries
        }
    
    def _fetch_interactions_from_ai(self, medicine_name: str, current_medications: List[str]) -> Dict[str, Any]:
        """Fetch interactions from AI when cache is not available"""
        current_meds_str = ", ".join(current_medications) if current_medications else "None"
        
        prompt = f"""
        As a medical AI assistant, analyze potential drug interactions between {medicine_name} and the following current medications: {current_meds_str}
        
        Return a JSON response:
        {{
            "medicine": "{medicine_name}",
            "current_medications": {json.dumps(current_medications)},
            "interactions": [
                {{
                    "medication": "Interacting medication name",
                    "severity": "Minor/Moderate/Major",
                    "description": "Description of interaction",
                    "management": "How to manage this interaction"
                }}
            ],
            "safe_combinations": ["List of safe medications from current list"],
            "recommendations": "Overall recommendations"
        }}
        
        Be thorough and accurate. Include severity levels and management strategies.
        Return only valid JSON without markdown formatting.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            response_text = response.text.strip()
            
            # Clean up response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            
            interaction_data = json.loads(response_text.strip())
            
            return {
                'success': True,
                'data': interaction_data,
                'source': 'ai',
                'model_used': 'gemini-1.5-flash'
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for interaction check: {e}")
            return {
                'success': False,
                'error': 'Failed to parse interaction information'
            }
            
        except Exception as e:
            logger.error(f"Drug interaction check error: {e}")
            
            # Fallback response for network errors
            return {
                'success': True,
                'data': {
                    'medicine': medicine_name,
                    'current_medications': current_medications,
                    'interactions': [],
                    'safe_combinations': current_medications,
                    'recommendations': "Unable to check interactions due to network error. Please consult your healthcare provider or pharmacist for drug interaction information.",
                    'error_fallback': True
                },
                'source': 'fallback'
            }
    
    # ... (keep all your existing methods unchanged)
    def _get_cached_result(self, normalized_query: str) -> Dict[str, Any]:
        """Get cached search result if available and fresh"""
        try:
            cache = MedicineSearchCache.objects.filter(
                Q(normalized_query=normalized_query) | 
                Q(normalized_query__icontains=normalized_query)
            ).first()
            
            if cache and not cache.is_stale():
                cache.increment_access()
                
                # Get medicines from cache
                cached_medicines = cache.medicines.all().order_by('cachedmedicineresult__order_index')
                
                return {
                    'success': True,
                    'data': {
                        'disease': cache.search_query,
                        'medicines': [self._medicine_to_dict(med) for med in cached_medicines],
                        'disclaimer': "This information is for educational purposes only. Always consult with a healthcare provider.",
                        'source': 'cache',
                        'cached_at': cache.created_at.isoformat()
                    }
                }
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    def _get_or_create_disease(self, disease_name: str) -> Disease:
        """Get or create disease object"""
        # Try exact match first
        disease = Disease.objects.filter(normalized_name=disease_name.lower().strip()).first()
        
        if not disease:
            # Try fuzzy matching for similar diseases
            all_diseases = Disease.objects.all()
            for existing_disease in all_diseases:
                similarity = fuzz.ratio(disease_name.lower(), existing_disease.normalized_name)
                if similarity > 85:  # High similarity threshold
                    logger.info(f"Found similar disease: {existing_disease.name} for {disease_name}")
                    return existing_disease
            
            # Create new disease
            disease = Disease.objects.create(name=disease_name.title())
            logger.info(f"Created new disease: {disease.name}")
        
        return disease
    
    def _get_existing_medicines_for_disease(self, disease: Disease) -> List[Medicine]:
        """Get existing medicines for a disease"""
        return [dm.medicine for dm in disease.medicine_treatments.all()]
    
    def _save_medicines_to_db(self, disease: Disease, ai_data: Dict) -> List[Medicine]:
        """Save medicine data to database"""
        saved_medicines = []
        
        for med_data in ai_data.get('medicines', []):
            try:
                # Check if medicine already exists
                medicine = Medicine.objects.filter(
                    name__iexact=med_data.get('name', '')
                ).first()
                
                if medicine:
                    # Update existing medicine
                    medicine.generic_name = med_data.get('generic_name') or medicine.generic_name
                    medicine.brand_names = med_data.get('brand_names', []) or medicine.brand_names
                    medicine.drug_class = med_data.get('drug_class') or medicine.drug_class
                    medicine.mechanism = med_data.get('mechanism') or medicine.mechanism
                    medicine.dosage = med_data.get('dosage') or medicine.dosage
                    medicine.administration = med_data.get('administration') or medicine.administration
                    medicine.side_effects = med_data.get('side_effects', []) or medicine.side_effects
                    medicine.contraindications = med_data.get('contraindications', []) or medicine.contraindications
                    medicine.drug_interactions = med_data.get('drug_interactions', []) or medicine.drug_interactions
                    medicine.monitoring = med_data.get('monitoring') or medicine.monitoring
                    medicine.fda_approved = med_data.get('fda_approved', True)
                    medicine.pregnancy_category = med_data.get('pregnancy_category') or medicine.pregnancy_category
                    medicine.last_updated_from_ai = timezone.now()
                    medicine.ai_source_version = "gemini-1.5-flash"
                    medicine.save()
                else:
                    # Create new medicine
                    medicine = Medicine.objects.create(
                        name=med_data.get('name', ''),
                        generic_name=med_data.get('generic_name'),
                        brand_names=med_data.get('brand_names', []),
                        drug_class=med_data.get('drug_class'),
                        mechanism=med_data.get('mechanism'),
                        dosage=med_data.get('dosage'),
                        administration=med_data.get('administration'),
                        side_effects=med_data.get('side_effects', []),
                        contraindications=med_data.get('contraindications', []),
                        drug_interactions=med_data.get('drug_interactions', []),
                        monitoring=med_data.get('monitoring'),
                        fda_approved=med_data.get('fda_approved', True),
                        pregnancy_category=med_data.get('pregnancy_category'),
                        ai_source_version="gemini-1.5-flash"
                    )
                
                # Create or update disease-medicine relationship
                disease_medicine, created = DiseaseMedicine.objects.get_or_create(
                    disease=disease,
                    medicine=medicine,
                    defaults={
                        'indication': med_data.get('indication'),
                        'is_first_line': med_data.get('is_first_line', False),
                        'generated_by_ai': True
                    }
                )
                
                if not created:
                    # Update existing relationship
                    disease_medicine.indication = med_data.get('indication') or disease_medicine.indication
                    disease_medicine.is_first_line = med_data.get('is_first_line', disease_medicine.is_first_line)
                    disease_medicine.save()
                
                saved_medicines.append(medicine)
                
            except Exception as e:
                logger.error(f"Error saving medicine {med_data.get('name', 'Unknown')}: {e}")
                continue
        
        return saved_medicines
    
    def _create_cache_entry(self, normalized_query: str, medicines: List[Medicine], ai_result: Dict):
        """Create cache entry for search result"""
        try:
            # Delete old cache entries for this query
            MedicineSearchCache.objects.filter(normalized_query=normalized_query).delete()
            
            # Create new cache entry
            cache = MedicineSearchCache.objects.create(
                search_query=ai_result['data']['disease'],
                total_results=len(medicines),
                ai_response_raw=ai_result.get('raw_response'),
                ai_processing_time=ai_result.get('processing_time')
            )
            
            # Add medicines to cache
            for index, medicine in enumerate(medicines):
                CachedMedicineResult.objects.create(
                    cache=cache,
                    medicine=medicine,
                    order_index=index
                )
                
        except Exception as e:
            logger.error(f"Error creating cache entry: {e}")
    
    def _format_cached_medicines(self, disease: Disease, medicines: List[Medicine]) -> Dict[str, Any]:
        """Format cached medicines for API response"""
        return {
            'success': True,
            'data': {
                'disease': disease.name,
                'medicines': [self._medicine_to_dict(med) for med in medicines],
                'disclaimer': "This information is for educational purposes only. Always consult with a healthcare provider.",
                'source': 'database',
                'last_updated': max([med.last_updated_from_ai for med in medicines]).isoformat() if medicines else None
            }
        }
    
    def _medicine_to_dict(self, medicine: Medicine) -> Dict[str, Any]:
        """Convert Medicine model to dictionary"""
        return {
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
            'last_searched': medicine.last_searched.isoformat() if medicine.last_searched else None
        }
    
    def get_drug_interactions_from_cache(self, medicine_name: str, current_medications: List[str]) -> Dict[str, Any]:
        """Check drug interactions using cached data first, then AI if needed"""
        try:
            # Get medicine object
            medicine = Medicine.objects.filter(name__iexact=medicine_name).first()
            if not medicine:
                return self._fetch_interactions_from_ai(medicine_name, current_medications)
            
            # Track search
            medicine.increment_search_count()
            
            # Check cached interactions
            cached_interactions = []
            for current_med in current_medications:
                current_med_obj = Medicine.objects.filter(name__icontains=current_med.strip()).first()
                if current_med_obj:
                    # Check both directions of interaction
                    interaction = MedicineInteraction.objects.filter(
                        Q(medicine_a=medicine, medicine_b=current_med_obj) |
                        Q(medicine_a=current_med_obj, medicine_b=medicine)
                    ).first()
                    
                    if interaction:
                        cached_interactions.append({
                            'medication': current_med,
                            'severity': interaction.get_severity_display(),
                            'description': interaction.description,
                            'management': interaction.management
                        })
            
            # If we have some cached data, return it
            if cached_interactions or not current_medications:
                safe_combinations = [med for med in current_medications 
                                   if not any(inter['medication'] == med for inter in cached_interactions)]
                
                return {
                    'success': True,
                    'data': {
                        'medicine': medicine_name,
                        'current_medications': current_medications,
                        'interactions': cached_interactions,
                        'safe_combinations': safe_combinations,
                        'recommendations': "Based on cached data. For most up-to-date information, consult your healthcare provider.",
                        'source': 'cache'
                    }
                }
            
            # Fallback to AI
            return self._fetch_interactions_from_ai(medicine_name, current_medications)
            
        except Exception as e:
            logger.error(f"Error checking cached interactions: {e}")
            return self._fetch_interactions_from_ai(medicine_name, current_medications)