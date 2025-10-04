from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from rpm_users.models import Patient, InterestLead
from reports.models import Reports
from rpm_users.models import  PastMedicalHistory
from django.utils import timezone
from datetime import timedelta
from .services import RetellCallService, GeminiSummaryService
from reports.models import Documentation
from .models import RetellCallSession, CallSummary, LeadCallSession, LeadCallSummary

logger = logging.getLogger('retell_calling.views')


@api_view(['POST'])
def trigger_call(request):
    """
    Trigger a call to a specific patient.
    
    Expected payload:
    {
        "patient_id": 123,
        "agent_id": "optional_agent_id"
    }
    """
    try:
        # Parse request data - use request.data for DRF @api_view
        data = request.data
        
        patient_id = data.get('patient_id')
        agent_id = data.get('agent_id')
        
        if not patient_id:
            return Response({
                'error': 'patient_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Triggering call for patient ID: {patient_id}")
        
        # Get the patient
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({
                'error': f'Patient with ID {patient_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize the call service
        call_service = RetellCallService()
        
        # Build dynamic variables for the agent flow
        one_month_ago = timezone.now() - timedelta(days=30)
        recent_reports = Reports.objects.filter(patient=patient).order_by('-created_at')[:20]

        # Compute vitals aggregates
        systolic_values = []
        diastolic_values = []
        reading_count = 0
        for r in recent_reports:
            try:
                if r.systolic_blood_pressure:
                    systolic_values.append(int(r.systolic_blood_pressure))
                if r.diastolic_blood_pressure:
                    diastolic_values.append(int(r.diastolic_blood_pressure))
            except Exception:
                pass
            reading_count += 1

        avg_systolic = round(sum(systolic_values) / len(systolic_values)) if systolic_values else None
        avg_diastolic = round(sum(diastolic_values) / len(diastolic_values)) if diastolic_values else None

        # Past medical history list
        pmh_list = list(PastMedicalHistory.objects.filter(patient=patient).values_list('pmh', flat=True))

        # Patient demographics/context (ensure all values are strings per Retell requirements)
        raw_dynamic_variables = {
            'patient_id': str(patient.id),
            'patient_name': f"{patient.user.first_name} {patient.user.last_name}".strip(),
            'patient_first_name': patient.user.first_name or '',
            'patient_last_name': patient.user.last_name or '',
            'patient_email': patient.user.email or '',
            'patient_phone': patient.phone_number or '',
            'dob': str(patient.date_of_birth) if patient.date_of_birth else '',
            'sex': patient.sex or '',
            'age': patient.age if hasattr(patient, 'age') else None,
            'monitoring_parameters': patient.monitoring_parameters or '',
            'allergies': patient.allergies or '',
            'medications': patient.medications or '',
            'pmh': pmh_list,
            # Recent BP summary for flow
            'systolic': avg_systolic,
            'diastolic': avg_diastolic,
            'readings': reading_count,
        }

        def _stringify(value):
            if isinstance(value, (list, tuple)):
                return ", ".join([str(v) for v in value if v is not None])
            if value is None:
                return ""
            return str(value)

        dynamic_variables = {k: _stringify(v) for k, v in raw_dynamic_variables.items()}

        # Create the call
        try:
            result = call_service.create_phone_call(patient, agent_id, dynamic_variables)
            
            return Response({
                'success': True,
                'message': 'Call initiated successfully',
                'call_id': result['call_id'],
                'call_session_id': result['call_session'].id,
                'patient': {
                    'id': patient.id,
                    'name': f"{patient.user.first_name} {patient.user.last_name}",
                    'phone': patient.phone_number
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            logger.error(f"Validation error creating call: {str(e)}")
            return Response({
                'error': f'Validation error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating call: {str(e)}")
            return Response({
                'error': f'Failed to create call: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON in request body'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in trigger_call: {str(e)}")
        return Response({
            'error': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def list_patients(request):
    """
    List all patients available for calling.
    """
    try:
        patients = Patient.objects.select_related('user').all()
        
        patient_list = []
        for patient in patients:
            patient_list.append({
                'id': patient.id,
                'name': f"{patient.user.first_name} {patient.user.last_name}",
                'email': patient.user.email,
                'phone': patient.phone_number,
                'has_phone': bool(patient.phone_number)
            })
        
        return Response({
            'patients': patient_list,
            'count': len(patient_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing patients: {str(e)}")
        return Response({
            'error': f'Failed to list patients: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def call_status(request, call_session_id):
    """
    Get the status of a specific call session.
    """
    try:
        call_session = RetellCallSession.objects.select_related('patient__user').get(id=call_session_id)
        
        return Response({
            'call_session_id': call_session.id,
            'retell_call_id': call_session.retell_call_id,
            'patient': {
                'id': call_session.patient.id,
                'name': f"{call_session.patient.user.first_name} {call_session.patient.user.last_name}"
            },
            'status': call_session.call_status,
            'from_number': call_session.from_number,
            'to_number': call_session.to_number,
            'start_timestamp': call_session.start_timestamp,
            'end_timestamp': call_session.end_timestamp,
            'duration_ms': call_session.duration_ms,
            'has_transcript': bool(call_session.transcript),
            'has_recording': bool(call_session.recording_url),
            'created_at': call_session.created_at,
            'updated_at': call_session.updated_at
        }, status=status.HTTP_200_OK)
        
    except RetellCallSession.DoesNotExist:
        return Response({
            'error': f'Call session with ID {call_session_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error getting call status: {str(e)}")
        return Response({
            'error': f'Failed to get call status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@require_http_methods(["POST"])
def retell_webhook(request):
    """
    Webhook endpoint to receive events from Retell AI.
    
    Handles call_started, call_ended, and call_analyzed events.
    Based on Retell AI webhook documentation.
    """
    print("webhook triggered")
    try:
        # Parse the webhook payload
        webhook_data = json.loads(request.body)
        
        event_type = webhook_data.get('event')
        call_data = webhook_data.get('call', {})
        
        logger.info(f"Received Retell webhook event: {event_type}")
        logger.debug(f"Full webhook payload: {webhook_data}")
        
        # Extract call information from the call object
        call_id = call_data.get('call_id')
        
        if not call_id:
            logger.error("No call_id in webhook payload")
            return JsonResponse({
                'error': 'call_id is required in call object'
            }, status=400)
        
        # Find the call session - check both patient and lead call sessions
        call_session = None
        call_type = None
        
        try:
            call_session = RetellCallSession.objects.get(retell_call_id=call_id)
            call_type = 'patient'
            logger.info(f"Found patient call session for call_id: {call_id}")
        except RetellCallSession.DoesNotExist:
            try:
                call_session = LeadCallSession.objects.get(retell_call_id=call_id)
                call_type = 'lead'
                logger.info(f"Found lead call session for call_id: {call_id}")
            except LeadCallSession.DoesNotExist:
                logger.error(f"Call session not found for call_id: {call_id}")
                return JsonResponse({
                    'error': f'Call session not found for call_id: {call_id}'
                }, status=404)
        
        # Update call session based on event type and call data
        if event_type == 'call_started':
            logger.info(f"Call started: {call_id}")
            call_session.call_status = 'in_progress'
            
            # Update start timestamp if provided
            if 'start_timestamp' in call_data:
                call_session.start_timestamp = call_data['start_timestamp']
                
        elif event_type == 'call_ended':
            logger.info(f"Call ended: {call_id}")
            
            # Update call session with end data
            call_session.call_status = call_data.get('call_status', 'completed')
            
            if 'start_timestamp' in call_data:
                call_session.start_timestamp = call_data['start_timestamp']
            
            if 'end_timestamp' in call_data:
                call_session.end_timestamp = call_data['end_timestamp']
            
            if 'disconnection_reason' in call_data:
                call_session.disconnection_reason = call_data['disconnection_reason']
            
            # Calculate duration if timestamps are available
            if call_data.get('start_timestamp') and call_data.get('end_timestamp'):
                duration_ms = call_data['end_timestamp'] - call_data['start_timestamp']
                call_session.duration_ms = duration_ms
            
            # Store transcript if available
            if 'transcript' in call_data and call_data['transcript']:
                call_session.transcript = call_data['transcript']
                logger.info(f"Transcript received for call {call_id}")
                logger.info(f"Transcript content: {call_data['transcript'][:500]}...")  # Log first 500 chars
            
            # Store transcript object if available (structured transcript)
            if 'transcript_object' in call_data:
                call_session.transcript_object = json.dumps(call_data['transcript_object'])
                logger.info(f"Structured transcript object stored for call {call_id}")
            
            # Store recording URL if available
            if 'recording_url' in call_data:
                call_session.recording_url = call_data['recording_url']
                logger.info(f"Recording URL stored for call {call_id}: {call_data['recording_url']}")
            
            # Process transcript with AI if available
            if call_session.transcript:
                logger.info(f"Processing transcript with AI for {call_type} call: {call_id}")
                
                try:
                    # Initialize Gemini service
                    gemini_service = GeminiSummaryService()
                    
                    # Prepare context based on call type
                    if call_type == 'patient':
                        context = {
                            'patient_name': call_session.patient.user.first_name,
                            'patient_id': call_session.patient.id
                        }
                    else:  # lead call
                        context = {
                            'lead_name': f"{call_session.lead.first_name or ''} {call_session.lead.last_name or ''}".strip(),
                            'lead_id': call_session.lead.id
                        }
                    
                    # Generate AI summary
                    summary_data = gemini_service.generate_summary(
                        call_session.transcript, 
                        context
                    )
                    
                    # Store the AI summary in the call session for backward compatibility
                    call_session.ai_summary = json.dumps(summary_data)
                    
                    if call_type == 'patient':
                        # Create or update CallSummary record for patient calls
                        call_summary, created = CallSummary.objects.get_or_create(
                            call_session=call_session,
                            defaults={
                                'patient': call_session.patient,
                                'summary_text': summary_data.get('summary', ''),
                                'key_points': summary_data.get('key_points', []),
                                'concerning_flags': summary_data.get('concerning_flags', []),
                                'health_metrics': summary_data.get('health_metrics', {}),
                                'ai_confidence_score': summary_data.get('confidence_score')
                            }
                        )
                        
                        if not created:
                            # Update existing summary
                            call_summary.summary_text = summary_data.get('summary', '')
                            call_summary.key_points = summary_data.get('key_points', [])
                            call_summary.concerning_flags = summary_data.get('concerning_flags', [])
                            call_summary.health_metrics = summary_data.get('health_metrics', {})
                            call_summary.ai_confidence_score = summary_data.get('confidence_score')
                            call_summary.save()
                        
                        # Also create a Documentation record with the summary text
                        try:
                            Documentation.objects.create(
                                patient=call_session.patient,
                                title='AI Note',
                                history_of_present_illness=summary_data.get('summary', ''),
                                written_by='AI Note',
                                doc_report_date=timezone.now().date(),
                            )
                            logger.info(f"Documentation created from AI summary for patient call: {call_id}")
                        except Exception as doc_err:
                            logger.error(f"Failed to create Documentation from AI summary for patient call {call_id}: {str(doc_err)}")
                    
                    else:  # lead call
                        # Create or update LeadCallSummary record for lead calls
                        from .models import LeadCallSummary
                        lead_call_summary, created = LeadCallSummary.objects.get_or_create(
                            call_session=call_session,
                            defaults={
                                'lead': call_session.lead,
                                'summary_text': summary_data.get('summary', ''),
                                'key_points': summary_data.get('key_points', []),
                                'concerning_flags': summary_data.get('concerning_flags', []),
                                'health_metrics': summary_data.get('health_metrics', {}),
                                'ai_confidence_score': summary_data.get('confidence_score')
                            }
                        )
                        
                        if not created:
                            # Update existing summary
                            lead_call_summary.summary_text = summary_data.get('summary', '')
                            lead_call_summary.key_points = summary_data.get('key_points', [])
                            lead_call_summary.concerning_flags = summary_data.get('concerning_flags', [])
                            lead_call_summary.health_metrics = summary_data.get('health_metrics', {})
                            lead_call_summary.ai_confidence_score = summary_data.get('confidence_score')
                            lead_call_summary.save()
                    
                    action = "created" if created else "updated"
                    logger.info(f"{'CallSummary' if call_type == 'patient' else 'LeadCallSummary'} {action} for {call_type} call: {call_id}")
                    logger.info(f"AI summary generated and stored for {call_type} call: {call_id}")
                    
                    # Log concerning flags if any
                    concerning_flags = summary_data.get('concerning_flags', [])
                    if concerning_flags:
                        logger.warning(f"CONCERNING FLAGS identified in {call_type} call {call_id}: {concerning_flags}")
                    
                    # Log key health metrics
                    health_metrics = summary_data.get('health_metrics', {})
                    if health_metrics:
                        logger.info(f"Health metrics extracted for {call_type} call {call_id}: {health_metrics}")
                    
                except Exception as e:
                    logger.error(f"Error processing transcript with AI for {call_type} call {call_id}: {str(e)}")
                    # Don't fail the webhook if AI processing fails
            
        elif event_type == 'call_analyzed':
            logger.info(f"Call analysis complete: {call_id}")
            
            # Store call analysis data if available
            if 'call_analysis' in call_data:
                call_session.call_analysis = json.dumps(call_data['call_analysis'])
                logger.info(f"Call analysis data stored for call {call_id}")
        
        # Save the updated call session
        call_session.save()
        
        logger.info(f"Call session updated successfully for call {call_id}, event: {event_type}")
        
        # Return success response (Retell expects 2xx status)
        return JsonResponse({
            'success': True,
            'message': 'Webhook processed successfully',
            'call_id': call_id,
            'event': event_type,
            'call_session_id': call_session.id
        }, status=200)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook payload: {str(e)}")
        return JsonResponse({
            'error': 'Invalid JSON payload'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error processing Retell webhook: {str(e)}")
        return JsonResponse({
            'error': f'Webhook processing failed: {str(e)}'
        }, status=500)


@api_view(['GET'])
def call_transcript(request, call_session_id):
    """
    Get the transcript and AI summary for a specific call session.
    """
    try:
        call_session = RetellCallSession.objects.select_related('patient__user').get(id=call_session_id)
        
        # Parse AI summary if available
        ai_summary = None
        if call_session.ai_summary:
            try:
                ai_summary = json.loads(call_session.ai_summary)
            except json.JSONDecodeError:
                logger.error(f"Invalid AI summary JSON for call session {call_session_id}")
        
        # Parse transcript object if available
        transcript_object = None
        if call_session.transcript_object:
            try:
                transcript_object = json.loads(call_session.transcript_object)
            except json.JSONDecodeError:
                logger.error(f"Invalid transcript object JSON for call session {call_session_id}")
        
        # Parse call analysis if available
        call_analysis = None
        if call_session.call_analysis:
            try:
                call_analysis = json.loads(call_session.call_analysis)
            except json.JSONDecodeError:
                logger.error(f"Invalid call analysis JSON for call session {call_session_id}")
        
        return Response({
            'call_session_id': call_session.id,
            'retell_call_id': call_session.retell_call_id,
            'patient': {
                'id': call_session.patient.id,
                'name': f"{call_session.patient.user.first_name} {call_session.patient.user.last_name}"
            },
            'transcript': call_session.transcript,
            'transcript_object': transcript_object,
            'ai_summary': ai_summary,
            'call_analysis': call_analysis,
            'recording_url': call_session.recording_url,
            'call_status': call_session.call_status,
            'disconnection_reason': call_session.disconnection_reason,
            'duration_ms': call_session.duration_ms,
            'start_timestamp': call_session.start_timestamp,
            'end_timestamp': call_session.end_timestamp
        }, status=status.HTTP_200_OK)
        
    except RetellCallSession.DoesNotExist:
        return Response({
            'error': f'Call session with ID {call_session_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error getting call transcript: {str(e)}")
        return Response({
            'error': f'Failed to get call transcript: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def process_transcript(request, call_session_id):
    """
    Manually trigger AI processing for a call transcript.
    Useful for reprocessing or processing calls that failed initial AI analysis.
    """
    try:
        call_session = RetellCallSession.objects.select_related('patient__user').get(id=call_session_id)
        
        if not call_session.transcript:
            return Response({
                'error': 'No transcript available for this call session'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Manually processing transcript for call session: {call_session_id}")
        
        # Initialize Gemini service
        gemini_service = GeminiSummaryService()
        
        # Prepare patient context
        patient_context = {
            'patient_name': call_session.patient.user.first_name,
            'patient_id': call_session.patient.id
        }
        
        # Generate AI summary
        summary_data = gemini_service.generate_summary(
            call_session.transcript, 
            patient_context
        )
        
        # Store the AI summary in the call session for backward compatibility
        call_session.ai_summary = json.dumps(summary_data)
        call_session.save()
        
        # Create or update CallSummary record
        call_summary, created = CallSummary.objects.get_or_create(
            call_session=call_session,
            defaults={
                'patient': call_session.patient,
                'summary_text': summary_data.get('summary', ''),
                'key_points': summary_data.get('key_points', []),
                'concerning_flags': summary_data.get('concerning_flags', []),
                'health_metrics': summary_data.get('health_metrics', {}),
                'ai_confidence_score': summary_data.get('confidence_score')
            }
        )
        
        if not created:
            # Update existing summary
            call_summary.summary_text = summary_data.get('summary', '')
            call_summary.key_points = summary_data.get('key_points', [])
            call_summary.concerning_flags = summary_data.get('concerning_flags', [])
            call_summary.health_metrics = summary_data.get('health_metrics', {})
            call_summary.ai_confidence_score = summary_data.get('confidence_score')
            call_summary.save()
        
        # Also create a Documentation record with the summary text
        try:
            Documentation.objects.create(
                patient=call_session.patient,
                title='AI Note',
                history_of_present_illness=summary_data.get('summary', ''),
                written_by='AI - Gemini',
                date_of_service=timezone.now().date(),
            )
            logger.info(f"Documentation created from AI summary for call session: {call_session_id}")
        except Exception as doc_err:
            logger.error(f"Failed to create Documentation from AI summary for call session {call_session_id}: {str(doc_err)}")
        
        action = "created" if created else "updated"
        logger.info(f"CallSummary {action} for call session: {call_session_id}")
        logger.info(f"AI summary manually generated for call session: {call_session_id}")
        
        return Response({
            'success': True,
            'message': 'Transcript processed successfully',
            'call_session_id': call_session.id,
            'call_summary_id': call_summary.id,
            'ai_summary': summary_data
        }, status=status.HTTP_200_OK)
        
    except RetellCallSession.DoesNotExist:
        return Response({
            'error': f'Call session with ID {call_session_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error processing transcript: {str(e)}")
        return Response({
            'error': f'Failed to process transcript: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def call_summaries_list(request):
    """
    Display all patients with their call summary counts for admin access.
    """
    try:
        # Get all patients with their call summary counts
        patients_with_calls = Patient.objects.select_related('user').annotate(
            call_count=models.Count('call_summaries'),
            latest_call=models.Max('call_summaries__generated_at')
        ).filter(call_count__gt=0).order_by('-latest_call')
        
        # Get patients without calls
        patients_without_calls = Patient.objects.select_related('user').annotate(
            call_count=models.Count('call_summaries')
        ).filter(call_count=0).order_by('user__first_name', 'user__last_name')
        
        context = {
            'patients_with_calls': patients_with_calls,
            'patients_without_calls': patients_without_calls,
            'total_summaries': CallSummary.objects.count(),
            'total_patients_with_calls': patients_with_calls.count(),
        }
        print(
            "context",context
        )
        return render(request, 'retell_calling/call_summaries_list.html', context)
        
    except Exception as e:
        logger.error(f"Error loading call summaries list: {str(e)}")
        messages.error(request, f'Error loading call summaries: {str(e)}')
        return redirect('admin_dashboard')


def patient_call_summaries(request, patient_id):
    """
    Display all call summaries and detailed call information for a specific patient.
    """
    try:
        patient = Patient.objects.select_related('user').get(id=patient_id)
        
        # Get all call summaries for this patient with related call session data
        call_summaries = CallSummary.objects.filter(patient=patient).select_related(
            'call_session'
        ).order_by('-generated_at')
        
        # Get call sessions without summaries (if any)
        call_sessions_without_summaries = RetellCallSession.objects.filter(
            patient=patient
        ).exclude(
            id__in=call_summaries.values_list('call_session_id', flat=True)
        ).order_by('-created_at')
        
        context = {
            'patient': patient,
            'call_summaries': call_summaries,
            'call_sessions_without_summaries': call_sessions_without_summaries,
            'total_calls': call_summaries.count() + call_sessions_without_summaries.count(),
            'total_summaries': call_summaries.count(),
        }
        
        return render(request, 'retell_calling/patient_call_summaries.html', context)
        
    except Patient.DoesNotExist:
        messages.error(request, f'Patient with ID {patient_id} not found.')
        return redirect('retell_calling:call_summaries_list')
    
    except Exception as e:
        logger.error(f"Error loading patient call summaries: {str(e)}")
        messages.error(request, f'Error loading patient call summaries: {str(e)}')
        return redirect('retell_calling:call_summaries_list')

def debug_call_summaries(request):
    """
    Debug view to check CallSummary records and their relationships.
    """
    try:
        # Get all call summaries with related data
        call_summaries = CallSummary.objects.select_related(
            'patient__user', 'call_session'
        ).all()
        
        # Get all call sessions
        call_sessions = RetellCallSession.objects.select_related(
            'patient__user'
        ).all()
        
        debug_data = {
            'total_call_summaries': call_summaries.count(),
            'total_call_sessions': call_sessions.count(),
            'call_summaries': [],
            'call_sessions_without_summaries': []
        }
        
        # Process call summaries
        for summary in call_summaries:
            debug_data['call_summaries'].append({
                'id': str(summary.id),
                'patient_name': f"{summary.patient.user.first_name} {summary.patient.user.last_name}",
                'patient_email': summary.patient.user.email,
                'summary_text': summary.summary_text[:100] + '...' if len(summary.summary_text) > 100 else summary.summary_text,
                'key_points_count': len(summary.key_points) if summary.key_points else 0,
                'concerning_flags_count': len(summary.concerning_flags) if summary.concerning_flags else 0,
                'health_metrics_count': len(summary.health_metrics) if summary.health_metrics else 0,
                'confidence_score': float(summary.ai_confidence_score) if summary.ai_confidence_score else None,
                'generated_at': summary.generated_at.isoformat(),
                'call_session_id': str(summary.call_session.id),
                'call_status': summary.call_session.call_status,
                'call_duration_minutes': summary.call_session.duration_minutes if summary.call_session.duration_ms else None
            })
        
        # Process call sessions without summaries
        sessions_with_summaries = call_summaries.values_list('call_session_id', flat=True)
        sessions_without_summaries = call_sessions.exclude(id__in=sessions_with_summaries)
        
        for session in sessions_without_summaries:
            debug_data['call_sessions_without_summaries'].append({
                'id': str(session.id),
                'patient_name': f"{session.patient.user.first_name} {session.patient.user.last_name}",
                'patient_email': session.patient.user.email,
                'call_status': session.call_status,
                'has_transcript': bool(session.transcript),
                'has_ai_summary': bool(session.ai_summary),
                'created_at': session.created_at.isoformat(),
                'call_duration_minutes': session.duration_minutes if session.duration_ms else None
            })
        
        return JsonResponse(debug_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error in debug_call_summaries: {str(e)}")
        return JsonResponse({
            'error': f'Debug failed: {str(e)}'
        }, status=500)


# Helper functions for sequential calling
def wait_for_call_completion(call_session, timeout=300):
    """
    Wait for a call to complete by polling the call session status.
    Returns True if call completed, False if timeout.
    """
    import time
    from .models import LeadCallSession
    
    start_time = time.time()
    logger.info(f"Waiting for call completion for session {call_session.id}")
    
    while time.time() - start_time < timeout:
        try:
            # Refresh the call session from database
            call_session.refresh_from_db()
            
            # Check if call is completed
            if call_session.is_completed:
                logger.info(f"Call completed with status: {call_session.call_status}")
                return True
                
            # Wait 5 seconds before checking again
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Error checking call status: {str(e)}")
            time.sleep(5)
    
    logger.warning(f"Call timeout after {timeout} seconds")
    return False


def generate_lead_call_summary(call_session):
    """
    Generate AI summary for a completed lead call.
    Returns True if successful, False otherwise.
    """
    try:
        from .models import LeadCallSummary
        from .services import GeminiSummaryService
        
        # Check if summary already exists
        if LeadCallSummary.objects.filter(call_session=call_session).exists():
            logger.info(f"Summary already exists for call session {call_session.id}")
            return True
        
        # Get the call transcript and metadata
        transcript = getattr(call_session, 'transcript', '') or ''
        call_duration = call_session.duration_seconds
        
        if not transcript:
            logger.warning(f"No transcript available for call session {call_session.id}")
            return False
        
        # Generate AI summary using Gemini
        summary_service = GeminiSummaryService()
        summary_data = summary_service.generate_summary(transcript, call_duration)
        
        if summary_data:
            # Create the lead call summary
            lead_call_summary = LeadCallSummary.objects.create(
                call_session=call_session,
                lead=call_session.lead,
                summary_text=summary_data.get('summary', ''),
                key_points=summary_data.get('key_points', []),
                concerning_flags=summary_data.get('concerning_flags', []),
                health_metrics=summary_data.get('health_metrics', {}),
                ai_confidence_score=summary_data.get('confidence_score')
            )
            
            logger.info(f"Created lead call summary for session {call_session.id}")
            return True
        else:
            logger.warning(f"Failed to generate summary data for call session {call_session.id}")
            return False
            
    except Exception as e:
        logger.error(f"Error generating lead call summary: {str(e)}")
        return False


# Lead Call Views
@api_view(['POST'])
def trigger_bulk_lead_calls(request):
    """
    Trigger sequential calls to all leads without existing calls.
    This will call one lead at a time, wait for completion, then move to the next.
    
    Expected payload:
    {
        "agent_id": "optional_agent_id"
    }
    """
    try:
        # Parse request data - use request.data for DRF @api_view
        data = request.data
        
        agent_id = "agent_f1e1852a2a6b90b39d997f95b5"
        
        logger.info("Starting sequential bulk calls to all leads")
        
        # Get leads without calls
        leads_without_calls = InterestLead.objects.annotate(
            call_count=models.Count('lead_call_sessions')
        ).filter(call_count=0).filter(phone_number__isnull=False).exclude(phone_number='')
        
        if not leads_without_calls.exists():
            return Response({
                'success': True,
                'message': 'No leads available for calling',
                'calls_initiated': 0,
                'leads': []
            }, status=status.HTTP_200_OK)
        
        # Initialize the call service
        call_service = RetellCallService()
        
        initiated_calls = []
        failed_calls = []
        
        # Process leads one by one
        for lead in leads_without_calls:
            try:
                logger.info(f"Starting call to lead {lead.id}: {lead.first_name} {lead.last_name}")
                
                # Build dynamic variables for the agent flow
                dynamic_variables = {
                    'lead_id': str(lead.id),
                    'lead_name': f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
                    'lead_first_name': lead.first_name or '',
                    'lead_last_name': lead.last_name or '',
                    'lead_email': lead.email or '',
                    'lead_phone': lead.phone_number or '',
                    'service_interest': lead.service_interest or '',
                    'insurance': lead.insurance or '',
                    'allergies': lead.allergies or '',
                    'additional_comments': lead.additional_comments or '',
                }
                
                # Create the call
                result = call_service.create_lead_call(lead, agent_id, dynamic_variables)
                
                call_session = result['call_session']
                call_id = result['call_id']
                
                logger.info(f"Call initiated for lead {lead.id}, call_id: {call_id}")
                
                # Wait for call to complete (polling approach)
                call_completed = wait_for_call_completion(call_session, timeout=300)  # 5 minute timeout
                
                if call_completed:
                    logger.info(f"Call completed for lead {lead.id}, generating summary...")
                    
                    # Generate summary for the completed call
                    try:
                        summary_result = generate_lead_call_summary(call_session)
                        if summary_result:
                            logger.info(f"Summary generated for lead {lead.id}")
                        else:
                            logger.warning(f"Failed to generate summary for lead {lead.id}")
                    except Exception as summary_error:
                        logger.error(f"Error generating summary for lead {lead.id}: {str(summary_error)}")
                    
                    initiated_calls.append({
                        'lead_id': lead.id,
                        'lead_name': f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
                        'phone': lead.phone_number,
                        'call_id': call_id,
                        'call_session_id': call_session.id,
                        'status': 'completed'
                    })
                else:
                    logger.warning(f"Call timeout for lead {lead.id}")
                    initiated_calls.append({
                        'lead_id': lead.id,
                        'lead_name': f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
                        'phone': lead.phone_number,
                        'call_id': call_id,
                        'call_session_id': call_session.id,
                        'status': 'timeout'
                    })
                
                logger.info(f"Completed processing lead {lead.id}, moving to next lead...")
                
            except Exception as e:
                logger.error(f"Failed to process lead {lead.id}: {str(e)}")
                failed_calls.append({
                    'lead_id': lead.id,
                    'lead_name': f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
                    'phone': lead.phone_number,
                    'error': str(e)
                })
        
        logger.info(f"Sequential bulk calling completed. {len(initiated_calls)} calls processed, {len(failed_calls)} failed.")
        
        return Response({
            'success': True,
            'message': f'Sequential bulk calling completed. {len(initiated_calls)} calls processed, {len(failed_calls)} failed.',
            'calls_initiated': len(initiated_calls),
            'calls_failed': len(failed_calls),
            'initiated_calls': initiated_calls,
            'failed_calls': failed_calls
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON in request body'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in trigger_bulk_lead_calls: {str(e)}")
        return Response({
            'error': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def trigger_lead_call(request):
    """
    Trigger a call to a specific lead.
    
    Expected payload:
    {
        "lead_id": 123,
        "agent_id": "optional_agent_id"
    }
    """
    try:
        # Parse request data - use request.data for DRF @api_view
        data = request.data
        
        lead_id = data.get('lead_id')
        agent_id = "agent_f1e1852a2a6b90b39d997f95b5"
        print("lead_id",lead_id)
        print("agent_id",agent_id)
        if not lead_id:
            return Response({
                'error': 'lead_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Triggering call for lead ID: {lead_id}")
        
        # Get the lead
        try:
            lead = InterestLead.objects.get(id=lead_id)
        except InterestLead.DoesNotExist:
            return Response({
                'error': f'Lead with ID {lead_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize the call service
        call_service = RetellCallService()
        
        # Build dynamic variables for the agent flow
        dynamic_variables = {
            'lead_id': str(lead.id),
            'lead_name': f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
            'lead_first_name': lead.first_name or '',
            'lead_last_name': lead.last_name or '',
            'lead_email': lead.email or '',
            'lead_phone': lead.phone_number or '',
            'service_interest': lead.service_interest or '',
            'insurance': lead.insurance or '',
            'allergies': lead.allergies or '',
            'additional_comments': lead.additional_comments or '',
        }
        print("dynamic_variables",dynamic_variables)
        # Create the call
        try:
            result = call_service.create_lead_call(lead, agent_id, dynamic_variables)
            print("result",result)
            return Response({
                'success': True,
                'message': 'Lead call initiated successfully',
                'call_id': result['call_id'],
                'call_session_id': result['call_session'].id,
                'lead': {
                    'id': lead.id,
                    'name': f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
                    'phone': lead.phone_number
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            logger.error(f"Validation error creating lead call: {str(e)}")
            return Response({
                'error': f'Validation error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating lead call: {str(e)}")
            return Response({
                'error': f'Failed to create lead call: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON in request body'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error in trigger_lead_call: {str(e)}")
        return Response({
            'error': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def leads_call_summaries_list(request):
    """
    Display all leads with their call summary counts for admin access.
    Supports search by name.
    """
    try:
        # Get search query
        search_query = request.GET.get('search', '').strip()
        
        # Base queryset for leads with calls
        leads_with_calls_qs = InterestLead.objects.annotate(
            call_count=models.Count('lead_call_summaries'),
            latest_call=models.Max('lead_call_summaries__generated_at')
        ).filter(call_count__gt=0)
        
        # Base queryset for leads without calls
        leads_without_calls_qs = InterestLead.objects.annotate(
            call_count=models.Count('lead_call_summaries')
        ).filter(call_count=0)
        
        # Apply search filter if provided
        if search_query:
            # Search by first name or last name (case insensitive)
            search_filter = models.Q(first_name__icontains=search_query) | models.Q(last_name__icontains=search_query)
            leads_with_calls_qs = leads_with_calls_qs.filter(search_filter)
            leads_without_calls_qs = leads_without_calls_qs.filter(search_filter)
        
        # Order the querysets
        leads_with_calls = leads_with_calls_qs.order_by('-latest_call')
        leads_without_calls = leads_without_calls_qs.order_by('first_name', 'last_name')
        
        context = {
            'leads_with_calls': leads_with_calls,
            'leads_without_calls': leads_without_calls,
            'total_summaries': LeadCallSummary.objects.count(),
            'total_leads_with_calls': leads_with_calls.count(),
            'search_query': search_query,
        }
        
        return render(request, 'retell_calling/leads_call_summaries_list.html', context)
        
    except Exception as e:
        logger.error(f"Error loading leads call summaries list: {str(e)}")
        messages.error(request, f'Error loading leads call summaries: {str(e)}')
        return redirect('admin_dashboard')


def lead_call_summaries(request, lead_id):
    """
    Display all call summaries and detailed call information for a specific lead.
    """
    try:
        lead = InterestLead.objects.get(id=lead_id)
        
        # Get all call summaries for this lead with related call session data
        call_summaries = LeadCallSummary.objects.filter(lead=lead).select_related(
            'call_session'
        ).order_by('-generated_at')
        
        # Get call sessions without summaries (if any)
        call_sessions_without_summaries = LeadCallSession.objects.filter(
            lead=lead
        ).exclude(
            id__in=call_summaries.values_list('call_session_id', flat=True)
        ).order_by('-created_at')
        
        context = {
            'lead': lead,
            'call_summaries': call_summaries,
            'call_sessions_without_summaries': call_sessions_without_summaries,
            'total_calls': call_summaries.count() + call_sessions_without_summaries.count(),
            'total_summaries': call_summaries.count(),
        }
        
        return render(request, 'retell_calling/lead_call_summaries.html', context)
        
    except InterestLead.DoesNotExist:
        messages.error(request, f'Lead with ID {lead_id} not found.')
        return redirect('leads_call_summaries')
    
    except Exception as e:
        logger.error(f"Error loading lead call summaries: {str(e)}")
        messages.error(request, f'Error loading lead call summaries: {str(e)}')
        return redirect('leads_call_summaries')