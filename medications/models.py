from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class Disease(models.Model):
    """Store disease information for medicine search caching"""
    name = models.CharField(max_length=255, unique=True, db_index=True)
    normalized_name = models.CharField(max_length=255, db_index=True)  # For fuzzy matching
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Normalize disease name for better matching
        self.normalized_name = self.name.lower().strip()
        super().save(*args, **kwargs)

class Medicine(models.Model):
    """Store comprehensive medicine information from Gemini AI"""
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    generic_name = models.CharField(max_length=255, blank=True, null=True)
    brand_names = models.JSONField(default=list, blank=True)  # List of brand names
    
    # Classification
    drug_class = models.CharField(max_length=255, blank=True, null=True)
    mechanism = models.TextField(blank=True, null=True)
    
    # Dosage Information
    dosage = models.TextField(blank=True, null=True)
    administration = models.TextField(blank=True, null=True)
    
    # Safety Information
    side_effects = models.JSONField(default=list, blank=True)  # List of side effects
    contraindications = models.JSONField(default=list, blank=True)  # List of contraindications
    drug_interactions = models.JSONField(default=list, blank=True)  # List of known interactions
    
    # Monitoring and Special Instructions
    monitoring = models.TextField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    
    # Regulatory Information
    fda_approved = models.BooleanField(default=True)
    pregnancy_category = models.CharField(max_length=10, blank=True, null=True)
    controlled_substance = models.BooleanField(default=False)
    
    # AI and Caching Information
    gemini_confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Gemini AI confidence score (0.00-1.00)"
    )
    last_updated_from_ai = models.DateTimeField(auto_now_add=True)
    ai_source_version = models.CharField(max_length=50, default="gemini-pro")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Search and Usage Stats
    search_count = models.PositiveIntegerField(default=0)
    last_searched = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['drug_class']),
            models.Index(fields=['last_searched']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.generic_name or 'N/A'})"
    
    def increment_search_count(self):
        """Increment search count and update last searched timestamp"""
        self.search_count += 1
        self.last_searched = timezone.now()
        self.save(update_fields=['search_count', 'last_searched'])
    
    def is_stale(self, days=30):
        """Check if medicine data is stale and needs refresh from AI"""
        if not self.last_updated_from_ai:
            return True
        return (timezone.now() - self.last_updated_from_ai).days > days
    
    def get_brand_names_display(self):
        """Get comma-separated brand names"""
        return ', '.join(self.brand_names) if self.brand_names else 'N/A'

class DiseaseMedicine(models.Model):
    """Many-to-many relationship between diseases and medicines with additional context"""
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='medicine_treatments')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='disease_indications')
    
    # Treatment Context
    indication = models.TextField(blank=True, null=True)  # Specific indication for this disease
    is_first_line = models.BooleanField(default=False)  # Is this a first-line treatment?
    is_off_label = models.BooleanField(default=False)  # Off-label use?
    
    # AI Generation Context
    generated_by_ai = models.BooleanField(default=True)
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['disease', 'medicine']
        ordering = ['-is_first_line', 'medicine__name']
    
    def __str__(self):
        return f"{self.medicine.name} for {self.disease.name}"

class MedicineSearchCache(models.Model):
    """Cache search results for faster subsequent searches"""
    search_query = models.CharField(max_length=500, unique=True, db_index=True)
    normalized_query = models.CharField(max_length=500, db_index=True)
    
    # Search Results
    medicines = models.ManyToManyField(Medicine, through='CachedMedicineResult')
    total_results = models.PositiveIntegerField(default=0)
    
    # Cache Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.PositiveIntegerField(default=0)
    
    # AI Context
    ai_response_raw = models.JSONField(blank=True, null=True)  # Store full AI response
    ai_processing_time = models.FloatField(null=True, blank=True)  # Time taken for AI response
    
    class Meta:
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"Cache: {self.search_query} ({self.total_results} results)"
    
    def save(self, *args, **kwargs):
        self.normalized_query = self.search_query.lower().strip()
        super().save(*args, **kwargs)
    
    def increment_access(self):
        """Update access stats"""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])
    
    def is_stale(self, hours=24):
        """Check if cache is stale"""
        return (timezone.now() - self.created_at).total_seconds() > (hours * 3600)

class CachedMedicineResult(models.Model):
    """Through model for MedicineSearchCache and Medicine relationship"""
    cache = models.ForeignKey(MedicineSearchCache, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    # Result Context
    relevance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    order_index = models.PositiveIntegerField(default=0)  # Order in search results
    
    class Meta:
        unique_together = ['cache', 'medicine']
        ordering = ['order_index']

class MedicineInteraction(models.Model):
    """Store known drug interactions between medicines"""
    medicine_a = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='interactions_as_a')
    medicine_b = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='interactions_as_b')
    
    # Interaction Details
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('contraindicated', 'Contraindicated'),
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    management = models.TextField(blank=True, null=True)
    
    # Clinical Context
    clinical_significance = models.TextField(blank=True, null=True)
    onset = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Rapid", "Delayed"
    documentation = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Well-documented"
    
    # AI and Source Information
    ai_generated = models.BooleanField(default=True)
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['medicine_a', 'medicine_b']
    
    def __str__(self):
        return f"{self.medicine_a.name} + {self.medicine_b.name} ({self.severity})"

class PatientMedicineHistory(models.Model):
    """Track which medicines were searched/viewed for which patients"""
    from rpm_users.models import Patient
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medicine_searches')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    disease_context = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Search Context
    search_query = models.CharField(max_length=500, blank=True)
    viewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Interaction
    interaction_checked = models.BooleanField(default=False)
    interaction_results = models.JSONField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} searched {self.medicine.name}"