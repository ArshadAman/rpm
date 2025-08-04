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

from rpm_users.models import Patient
from .services import RetellCallService, GeminiSummaryService
from .models import RetellCallSession, CallSummary

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
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
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
        
        # Create the call
        try:
            result = call_service.create_phone_call(patient, agent_id)
            
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
        
        # Find the call session
        try:
            call_session = RetellCallSession.objects.get(retell_call_id=call_id)
        except RetellCallSession.DoesNotExist:
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
                logger.info(f"Processing transcript with AI for call: {call_id}")
                
                try:
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
                    
                    action = "created" if created else "updated"
                    logger.info(f"CallSummary {action} for call: {call_id}")
                    logger.info(f"AI summary generated and stored for call: {call_id}")
                    
                    # Log concerning flags if any
                    concerning_flags = summary_data.get('concerning_flags', [])
                    if concerning_flags:
                        logger.warning(f"CONCERNING FLAGS identified in call {call_id}: {concerning_flags}")
                    
                    # Log key health metrics
                    health_metrics = summary_data.get('health_metrics', {})
                    if health_metrics:
                        logger.info(f"Health metrics extracted for call {call_id}: {health_metrics}")
                    
                except Exception as e:
                    logger.error(f"Error processing transcript with AI for call {call_id}: {str(e)}")
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