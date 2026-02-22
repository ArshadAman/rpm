
from django.core.management.base import BaseCommand
from rpm_users.models import LabCategory, LabTest
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds initial lab categories and tests'

    def handle(self, *args, **kwargs):
        lab_data = {
            "CBC": [
                "WBC", "RBC", "Hemoglobin", "Hematocrit", "MCV", "MCH", "MCHC", "RDW", "Platelets",
                "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils"
            ],
            "CMP": [
                "Glucose", "BUN", "Creatinine", "Sodium", "Potassium", "Chloride", "Carbon Dioxide",
                "Calcium", "Protein, Total", "Albumin", "Globulin", "A/G Ratio", "Bilirubin, Total",
                "Alkaline Phosphatase", "AST (SGOT)", "ALT (SGPT)"
            ],
            "Lipid Panel": [
                "Cholesterol, Total", "Triglycerides", "HDL Cholesterol", "VLDL Cholesterol (cal)",
                "LDL Cholesterol (calc)"
            ],
            "Thyroid": [
                "TSH", "T4, Free", "T3, Free"
            ],
            "Diabetes": [
                "Hemoglobin A1c", "Estimated Average Glucose"
            ],
            "Renal": [
                "eGFR", "Creatinine", "BUN/Creatinine Ratio"
            ],
            "Cardiac": [
                "Troponin I", "CK-MB", "BNP"
            ],
            "Urinalysis": [
                "Color", "Appearance", "Specific Gravity", "pH", "Protein", "Glucose", "Ketones",
                "Occult Blood", "Bilirubin", "Urobilinogen", "Nitrite", "Leukocyte Esterase",
                "WBC", "RBC", "Squamous Epithelial Cells", "Bacteria", "Hyaline Casts"
            ]
        }

        for category_name, tests in lab_data.items():
            category, created = LabCategory.objects.get_or_create(
                slug=slugify(category_name),
                defaults={'name': category_name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category_name}'))
            else:
                self.stdout.write(f'Category exists: {category_name}')

            for test_name in tests:
                test, created = LabTest.objects.get_or_create(
                    category=category,
                    name=test_name
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created test: {test_name}'))
                
        self.stdout.write(self.style.SUCCESS('Successfully seeded lab data'))
