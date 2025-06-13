#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rpm.settings')
django.setup()

from django.contrib.auth.models import User
from rpm_users.models import Patient, Doctor, Moderator
from rpm_users.signals import determine_user_type, get_email_template_data
import tempfile

def test_user_type_detection():
    """Test user type detection logic"""
    print("Testing user type detection...")
    
    # Create a test user
    test_user = User(
        username='testuser',
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    
    # Test default (patient) type
    user_type = determine_user_type(test_user)
    print(f"Default user type: {user_type}")
    
    # Test staff user (moderator)
    test_user.is_staff = True
    user_type = determine_user_type(test_user)
    print(f"Staff user type: {user_type}")
    
    # Test superuser (moderator)
    test_user.is_staff = False
    test_user.is_superuser = True
    user_type = determine_user_type(test_user)
    print(f"Superuser type: {user_type}")
    
    print("User type detection test completed!\n")

def test_email_template_data():
    """Test email template data generation"""
    print("Testing email template data generation...")
    
    test_user = User(
        username='testdoctor',
        email='doctor@example.com',
        first_name='Dr. John',
        last_name='Smith'
    )
    
    # Test doctor template
    template, subject, context = get_email_template_data(test_user, 'doctor')
    print(f"Doctor template: {template}")
    print(f"Doctor subject: {subject}")
    print(f"Doctor features count: {len(context['features'])}")
    
    # Test patient template
    template, subject, context = get_email_template_data(test_user, 'patient')
    print(f"Patient template: {template}")
    print(f"Patient subject: {subject}")
    print(f"Patient features count: {len(context['features'])}")
    
    # Test moderator template
    template, subject, context = get_email_template_data(test_user, 'moderator')
    print(f"Moderator template: {template}")
    print(f"Moderator subject: {subject}")
    print(f"Moderator features count: {len(context['features'])}")
    
    print("Email template data test completed!\n")

if __name__ == "__main__":
    print("=== RPM Email Signal System Test ===\n")
    test_user_type_detection()
    test_email_template_data()
    print("=== All tests completed successfully! ===")
