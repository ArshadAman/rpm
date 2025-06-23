from django.core.management.base import BaseCommand
from voice_bot.models import VoiceQuestion, AIKnowledgeBase

class Command(BaseCommand):
    help = 'Populate voice bot with sample questions and knowledge base'

    def handle(self, *args, **options):
        # Sample Voice Questions
        sample_questions = [
            {
                'question_type': 'health_check',
                'question_text': 'How are you feeling today on a scale of 1 to 10?',
                'expected_response_type': 'scale_1_10',
                'priority': 1
            },
            {
                'question_type': 'symptom_inquiry',
                'question_text': 'Have you experienced any chest pain or shortness of breath in the last 24 hours?',
                'expected_response_type': 'yes_no',
                'priority': 2
            },
            {
                'question_type': 'medication_adherence',
                'question_text': 'Have you taken all your prescribed medications today?',
                'expected_response_type': 'yes_no',
                'priority': 3
            },
            {
                'question_type': 'vital_signs',
                'question_text': 'Have you checked your blood pressure today? If so, what were the readings?',
                'expected_response_type': 'open_text',
                'priority': 4
            },
            {
                'question_type': 'satisfaction',
                'question_text': 'How satisfied are you with your RPM care on a scale of 1 to 10?',
                'expected_response_type': 'scale_1_10',
                'priority': 5
            }
        ]

        for question_data in sample_questions:
            question, created = VoiceQuestion.objects.get_or_create(
                question_text=question_data['question_text'],
                defaults=question_data
            )
            if created:
                self.stdout.write(f"Created question: {question.question_text}")

        # Sample Knowledge Base
        sample_knowledge = [
            {
                'knowledge_type': 'rpm_general',
                'title': 'What is Remote Patient Monitoring?',
                'content': 'Remote Patient Monitoring (RPM) is a healthcare technology that allows patients to use mobile medical devices to perform routine tests and send the test data to their healthcare providers in real-time.',
                'keywords': ['rpm', 'remote monitoring', 'healthcare technology', 'medical devices']
            },
            {
                'knowledge_type': 'emergency_protocols',
                'title': 'When to Seek Emergency Care',
                'content': 'Seek immediate emergency care if you experience: severe chest pain, difficulty breathing, sudden severe headache, signs of stroke, severe allergic reactions, or any symptoms that feel life-threatening.',
                'keywords': ['emergency', 'chest pain', 'breathing problems', 'stroke', 'urgent care']
            },
            {
                'knowledge_type': 'medical_conditions',
                'title': 'Managing Hypertension',
                'content': 'High blood pressure can be managed through medication adherence, regular monitoring, healthy diet (low sodium), regular exercise, stress management, and avoiding tobacco and excessive alcohol.',
                'keywords': ['hypertension', 'high blood pressure', 'medication', 'diet', 'exercise']
            },
            {
                'knowledge_type': 'faq',
                'title': 'How often should I check my vital signs?',
                'content': 'The frequency of vital sign monitoring depends on your specific condition and your healthcare provider\'s recommendations. Generally, blood pressure should be checked daily if you have hypertension, and weight should be monitored regularly if you have heart conditions.',
                'keywords': ['vital signs', 'blood pressure', 'monitoring frequency', 'daily checks']
            },
            {
                'knowledge_type': 'medication_info',
                'title': 'Importance of Medication Adherence',
                'content': 'Taking medications as prescribed is crucial for managing chronic conditions. Skipping doses can lead to complications. If you experience side effects or have concerns about your medications, contact your healthcare provider rather than stopping them on your own.',
                'keywords': ['medication adherence', 'prescribed medications', 'side effects', 'compliance']
            }
        ]

        for kb_data in sample_knowledge:
            knowledge, created = AIKnowledgeBase.objects.get_or_create(
                title=kb_data['title'],
                defaults=kb_data
            )
            if created:
                self.stdout.write(f"Created knowledge base entry: {knowledge.title}")

        self.stdout.write(
            self.style.SUCCESS('Successfully populated voice bot data!')
        )
