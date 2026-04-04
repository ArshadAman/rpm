# RPM: Remote Patient Monitoring System

[![Django](https://img.shields.io/badge/Django-4.2+-092e20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis)](https://redis.io/)
[![Gemini AI](https://img.shields.io/badge/Gemini%20AI-2.0%20Flash-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://ai.google.dev/)
[![Celery](https://img.shields.io/badge/Celery-Task%20Queue-37814A?style=for-the-badge&logo=celery)](https://docs.celeryq.dev/)

A sophisticated, production-ready Remote Patient Monitoring (RPM) platform designed for healthcare providers. This system integrates cutting-edge AI for medication safety, automated patient outreach, and real-time health data monitoring.

---

## 🌟 Key Features

### 🩺 Comprehensive Patient Management
- **Role-Based Dashboards**: Tailored interfaces for Administrators, Doctors, and Patient Moderators.
- **Intelligent Onboarding**: Multi-step registration for patients with detailed medical history tracking.
- **Moderator Assignment**: Automated and manual assignment of patients to health moderators for personalized care.
- **Escalation Protocol**: Direct Doctor-escalation system for high-priority patient health alerts.

### 🤖 AI-Powered MedInsight Engine
- **Smart Medicine Search**: Leverages **Google Gemini 2.0 Flash** to provide instant, detailed pharmaceutical data including drug classes, mechanisms, and FDA status.
- **Automated Interaction Checks**: Real-time cross-referencing of new prescriptions against a patient's current medication list to identify contraindications.
- **Clinical Signifance Filtering**: Intelligent severity categorization (Minor, Moderate, Major, Contraindicated) for drug-drug interactions.

### 📞 Automated Outreach & Calling
- **Retell AI Integration**: State-of-the-art AI voice agents handle patient follow-ups, lead qualification, and appointment reminders.
- **Twilio SMS/Voice**: Integrated communication layer for automated alerts and manual outreach.
- **Call Summarization**: Automated transcription and AI analysis of patient calls to extract key health metrics.

### 📊 Reporting & Analytics
- **Dynamic Report Generation**: Automated generation of health summaries and progress reports.
- **Cache Performance Analytics**: High-level observability into AI hit rates and median resolution times.

---

## ⚙️ Technical Architecture: The Caching Strategy

The most critical technical component of the RPM system is its **Multi-Layer Intelligent Caching Architecture**, designed to minimize AI latency, reduce API costs, and ensure high availability of medical data.

### 1. Database-Backed Permanent Caching (Persistent AI)
The `medications` app implements a persistent cache layer in PostgreSQL. When a search for a disease is performed:
- **Fuzzy Search & Normalization**: Queries are normalized and matched using `fuzzywuzzy` logic against existing `Disease` records (85% similarity threshold).
- **Relational Mapping**: Search results are stored in a `MedicineSearchCache` through-model, preserving result order and relevance scores.
- **Staleness Logic**: Data is automatically flagged as "stale" after a configurable period (default 30 days for medicines, 24 hours for search queries), triggering an asynchronous background refresh.

### 2. Fast Application Caching (Redis)
Utilizing `django-redis` for high-speed, volatile data:
- **Session Management**: Distributed session storage for seamless horizontal scaling.
- **Rate Limiting**: Integrated `django-ratelimit` to protect AI endpoints and authentication routes.
- **Celery Broker**: Low-latency message passing for the background task ecosystem.

### 3. Interaction Matrix Caching
To avoid redundant AI calls for common drug combinations:
- The system builds a **Medicine Interaction Matrix** in the database.
- Once an interaction (e.g., Aspirin + Warfarin) is analyzed by Gemini, it is cached permanently.
- Future checks for the same combination are resolved instantly from the local database.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Django 4.2 (Python 3.11+) |
| **Primary Database** | PostgreSQL 14 |
| **Cache & Message Broker** | Redis 7 (Alpine) |
| **Task Queue** | Celery (with Gevent/Concurrency) |
| **AI (LLM)** | Google Gemini 2.0 Flash |
| **AI (Voice)** | Retell AI API |
| **Infrastructure** | Docker, Nginx, Certbot (SSL), Dozzle (Logs) |
| **Cloud Services** | SendGrid (Email API), Twilio (SMS/Voice), Cloudinary (Media) |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Gemini AI API Key
- Retell AI Bearer Token

### Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/rpm-system.git
   cd rpm-system
   ```

2. **Configure Environment**:
   Create a `.env` file from the provided template:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Deploy with Docker**:
   ```bash
   # Build and start all services
   docker-compose up -d --build
   ```

4. **Initialize Database**:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the platform**:
   - **Main Web App**: `http://localhost:8000`
   - **Admin Dashboard**: `http://localhost:8000/admin_login/`
   - **Live Logs (Dozzle)**: `http://localhost:8080/logs`

---

## 📜 Development & Maintenance

### Background Tasks
The system relies on Celery for heavy lifting.
- **Worker**: `docker-compose logs -f celery`
- **Periodic Tasks (Beat)**: `docker-compose logs -f celery-beat`

### Log Management
- Application logs are stored in `./logs/django.log`.
- Container health can be monitored via the Dozzle dashboard.

### Security
- **SSL**: Automated via Certbot and Nginx.
- **JWT**: Secure API authentication via `rest_framework_simplejwt`.
- **CSRF**: Strict cookie-based protection for production domains.

---

> [!IMPORTANT]
> **Medical Disclaimer**: This software is intended for health monitoring and administrative support. AI-generated medication data should *always* be verified by a qualified healthcare professional before clinical use.
