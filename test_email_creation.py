#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rpm.settings')
django.setup()

from django.contrib.auth.models import User
from rpm_users.models import Patient, Doctor

def test_email_sending():
    """Test the actual email sending with different user types"""
    print("=== Testing Email Sending ===\n")
    
    # Test 1: Create a patient user
    print("1. Testing Patient Account Creation Email...")
    try:
        patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Create patient profile
        Patient.objects.create(
            user=patient_user,
            date_of_birth='1990-01-01',
            phone_number='1234567890'
        )
        
        print("✓ Patient user created successfully")
        print(f"  Email: {patient_user.email}")
        print(f"  Name: {patient_user.first_name} {patient_user.last_name}")
        
    except Exception as e:
        print(f"✗ Error creating patient: {e}")
    
    # Test 2: Create a doctor user
    print("\n2. Testing Doctor Account Creation Email...")
    try:
        doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@example.com',
            password='testpass123',
            first_name='Dr. Sarah',
            last_name='Wilson'
        )
        
        # Create doctor profile
        Doctor.objects.create(
            user=doctor_user,
            specialization='Cardiology',
            phone_number='0987654321'
        )
        
        print("✓ Doctor user created successfully")
        print(f"  Email: {doctor_user.email}")
        print(f"  Name: {doctor_user.first_name} {doctor_user.last_name}")
        
    except Exception as e:
        print(f"✗ Error creating doctor: {e}")
    
    # Test 3: Create a moderator user
    print("\n3. Testing Moderator Account Creation Email...")
    try:
        moderator_user = User.objects.create_user(
            username='testmoderator',
            email='moderator@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='Smith',
            is_staff=True
        )
        
        print("✓ Moderator user created successfully")
        print(f"  Email: {moderator_user.email}")
        print(f"  Name: {moderator_user.first_name} {moderator_user.last_name}")
        print(f"  Is Staff: {moderator_user.is_staff}")
        
    except Exception as e:
        print(f"✗ Error creating moderator: {e}")
    
    print("\n=== Email sending test completed! ===")
    print("Note: Check your console/email backend for the actual email content.")

def cleanup_test_users():
    """Clean up test users"""
    test_usernames = ['testpatient', 'testdoctor', 'testmoderator']
    deleted_count = 0
    
    for username in test_usernames:
        try:
            user = User.objects.get(username=username)
            user.delete()
            deleted_count += 1
            print(f"✓ Deleted user: {username}")
        except User.DoesNotExist:
            pass
        except Exception as e:
            print(f"✗ Error deleting {username}: {e}")
    
    print(f"\nCleaned up {deleted_count} test users.")

if __name__ == "__main__":
    # Clean up any existing test users first
    print("Cleaning up existing test users...")
    cleanup_test_users()
    
    # Test email sending
    test_email_sending()
    
    # Offer to clean up
    print("\nTest users created. Remember to clean them up when done testing.")
