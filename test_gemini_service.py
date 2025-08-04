#!/usr/bin/env python
"""
Test script for GeminiSummaryService
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rpm.settings')
django.setup()

from retell_calling.services import GeminiSummaryService

def test_gemini_service():
    """Test the GeminiSummaryService with a sample transcript"""
    
    # Sample transcript for testing
    sample_transcript = """
    Healthcare Provider: Hello, this is Dr. Shaiquel calling to check on how you're feeling today.
    
    Patient: Hi Dr.Shaiquel . I'm doing okay, but I've been having some pain in my lower back. It's about a 6 out of 10.
    
    Healthcare Provider: I see. Have you been taking your prescribed medication as directed?
    
    Patient: Yes, I've been taking the ibuprofen twice a day as you told me. It helps a little bit.
    
    Healthcare Provider: That's good. Any other symptoms or concerns?
    
    Patient: Well, I've been feeling a bit down lately. Not sleeping well either.
    
    Healthcare Provider: I understand. Let's schedule a follow-up appointment to discuss this further.
    
    Patient: That sounds good. Thank you, doctor.
    """
    
    try:
        # Initialize the service
        print("Initializing GeminiSummaryService...")
        service = GeminiSummaryService()
        print("✓ Service initialized successfully")
        
        # Test generate_summary
        print("\nTesting generate_summary...")
        patient_context = {'patient_name': 'John Doe'}
        summary = service.generate_summary(sample_transcript, patient_context)
        print("✓ Summary generated successfully")
        print(f"Summary: {summary.get('summary', 'N/A')}")
        print(f"Key points: {len(summary.get('key_points', []))} items")
        print(f"Concerning flags: {len(summary.get('concerning_flags', []))} items")
        print(f"Confidence score: {summary.get('confidence_score', 'N/A')}")
        
        # Test extract_health_metrics
        print("\nTesting extract_health_metrics...")
        health_metrics = service.extract_health_metrics(sample_transcript)
        print("✓ Health metrics extracted successfully")
        print(f"Health metrics keys: {list(health_metrics.keys())}")
        
        # Test identify_concerning_flags
        print("\nTesting identify_concerning_flags...")
        concerning_flags = service.identify_concerning_flags(sample_transcript)
        print("✓ Concerning flags identified successfully")
        print(f"Number of concerning flags: {len(concerning_flags)}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_service()
    sys.exit(0 if success else 1)