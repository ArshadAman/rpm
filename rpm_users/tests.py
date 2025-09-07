from django.test import TestCase
from .models import PastMedicalHistory

class PastMedicalHistoryTestCase(TestCase):
    def test_pmh_choices_have_unique_codes(self):
        """Test that all PMH choice codes are unique to prevent HTML ID conflicts"""
        choices = PastMedicalHistory.PMH_CHOICES
        codes = [choice[0] for choice in choices]
        
        # Check that all codes are unique
        self.assertEqual(len(codes), len(set(codes)), 
                        "PMH choice codes must be unique to prevent HTML ID conflicts")
        
        # Specifically test that Pancreatic and Prostate cancer have different codes
        pancreatic_code = None
        prostate_code = None
        
        for code, label in choices:
            if label == 'Pancreatic Cancer':
                pancreatic_code = code
            elif label == 'Prostate Cancer':
                prostate_code = code
        
        self.assertIsNotNone(pancreatic_code, "Pancreatic Cancer should be in PMH choices")
        self.assertIsNotNone(prostate_code, "Prostate Cancer should be in PMH choices")
        self.assertNotEqual(pancreatic_code, prostate_code, 
                           "Pancreatic Cancer and Prostate Cancer must have different codes")
