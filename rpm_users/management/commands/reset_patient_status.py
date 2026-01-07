from django.core.management.base import BaseCommand
from rpm_users.models import Patient
from django.utils import timezone


class Command(BaseCommand):
    help = 'Reset all patient statuses to green on the 1st of every month'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Check if today is the 1st of the month
        if today.day == 1:
            # Reset all patient statuses to green
            updated_count = Patient.objects.all().update(status='green')
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reset status for {updated_count} patients to green')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Today is not the 1st of the month (today is {today.day}). No status reset performed.')
            )
            self.stdout.write(
                self.style.NOTICE('Use --force to reset statuses regardless of date.')
            )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reset statuses regardless of date',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        if options['force'] or today.day == 1:
            # Reset all patient statuses to green
            updated_count = Patient.objects.all().update(status='green')
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reset status for {updated_count} patients to green')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Today is not the 1st of the month (today is day {today.day}). No status reset performed.')
            )
            self.stdout.write(
                self.style.NOTICE('Use --force to reset statuses regardless of date.')
            )
