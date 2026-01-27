from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from rpm_users.models import Patient, Doctor, Moderator, LabResult, LabTest, LabCategory
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Seeds the database with demo users (Doctor, Moderator, Patient) and lab data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding demo data...')

        # 1. Create Groups if they don't exist
        doctor_group, _ = Group.objects.get_or_create(name='Doctor')
        moderator_group, _ = Group.objects.get_or_create(name='Moderator')
        patient_group, _ = Group.objects.get_or_create(name='Patient')

        # 2. Create Doctor
        doc_user, created = User.objects.get_or_create(username='demo_doctor', email='doctor@demo.com')
        if created:
            doc_user.set_password('demo12345')
            doc_user.first_name = 'Dr. Gregory'
            doc_user.last_name = 'House'
            doc_user.save()
            doc_user.groups.add(doctor_group)
            Doctor.objects.create(user=doc_user, specialization='Diagnostician', phone_number='555-0101')
            self.stdout.write(self.style.SUCCESS(f'Created Doctor: {doc_user.username} / demo12345'))
        else:
            self.stdout.write(f'Doctor {doc_user.username} already exists')

        # 3. Create Moderator
        mod_user, created = User.objects.get_or_create(username='demo_moderator', email='mod@demo.com')
        if created:
            mod_user.set_password('demo12345')
            mod_user.first_name = 'Lisa'
            mod_user.last_name = 'Cuddy'
            mod_user.save()
            mod_user.groups.add(moderator_group)
            Moderator.objects.create(user=mod_user, phone_number='555-0102')
            self.stdout.write(self.style.SUCCESS(f'Created Moderator: {mod_user.username} / demo12345'))
        else:
            self.stdout.write(f'Moderator {mod_user.username} already exists')

        # 4. Create Patient
        pat_user, created = User.objects.get_or_create(username='demo_patient', email='patient@demo.com')
        patient = None
        if created:
            pat_user.set_password('demo12345')
            pat_user.first_name = 'John'
            pat_user.last_name = 'Doe'
            pat_user.save()
            pat_user.groups.add(patient_group)
            
            # Get instances
            mod_instance = Moderator.objects.get(user=mod_user)
            doc_instance = Doctor.objects.get(user=doc_user)

            patient = Patient.objects.create(
                user=pat_user,
                date_of_birth=date(1980, 5, 15),
                sex='Male',
                phone_number='555-0103',
                height=180,
                weight=75,
                insurance='Demo Health',
                insurance_number='DH-123456789',
                moderator_assigned=mod_instance,
                doctor_escalated=doc_instance,
                is_escalated=True, # Escalate so they appear in lists
                status='red'
            )
            self.stdout.write(self.style.SUCCESS(f'Created Patient: {pat_user.username} / demo12345'))
        else:
            self.stdout.write(f'Patient {pat_user.username} already exists')
            try:
                patient = Patient.objects.get(user=pat_user)
            except Patient.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Patient profile missing for {pat_user.username}'))

        # 5. Seed Lab Results for Patient
        if patient:
            self.seed_labs(patient)

    def seed_labs(self, patient):
        self.stdout.write('Seeding lab results...')
        
        # Get common categories/tests (assumes seed_labs was run or compatible data exists)
        try:
            cbc = LabCategory.objects.get(name='CBC')
            cmp = LabCategory.objects.get(name='CMP')
            
            wbc = LabTest.objects.filter(category=cbc, name__icontains='WBC').first()
            hgb = LabTest.objects.filter(category=cbc, name__icontains='Hemoglobin').first()
            glucose = LabTest.objects.filter(category=cmp, name__icontains='Glucose').first()
            
            tests_to_seed = [
                (wbc, '5.5', '7.2', 'Low count vs higher count'),
                (hgb, '14.0', '13.8', 'Stable'),
                (glucose, '95', '110', 'Post-prandial spike?'),
            ]

            today = date.today()
            
            for test, val1, val2, note in tests_to_seed:
                if not test: continue
                
                # Result 1 (Older)
                LabResult.objects.get_or_create(
                    patient=patient,
                    test=test,
                    date_recorded=today - timedelta(days=10),
                    defaults={
                        'value': val1,
                        'notes': f'Historical: {note}'
                    }
                )
                
                # Result 2 (Recent)
                LabResult.objects.get_or_create(
                    patient=patient,
                    test=test,
                    date_recorded=today - timedelta(days=1),
                    defaults={
                        'value': val2,
                        'notes': f'Recent: {note}'
                    }
                )
            
            self.stdout.write(self.style.SUCCESS('seeded lab results'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to seed labs (ensure structure exists): {e}'))

