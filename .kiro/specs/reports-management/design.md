# Design Document

## Overview

This design outlines the implementation of report management functionality for the RPM patient dashboard. The solution will add edit and create capabilities directly to the vitals summary table, providing healthcare moderators with seamless report management tools.

## Architecture

### Frontend Components
- **Report Management UI**: Icons and modals integrated into the existing vitals table
- **Modal Forms**: Reusable form components for both edit and create operations
- **Validation Layer**: Client-side validation with real-time feedback
- **State Management**: JavaScript-based state handling for form data and UI updates

### Backend Components
- **API Endpoints**: New endpoints for report CRUD operations
- **Data Validation**: Server-side validation for vital signs data
- **Permission Handling**: Moderator-only access controls
- **Database Operations**: Optimized queries for report management

## Components and Interfaces

### 1. Frontend UI Components

#### Report Management Toolbar
```html
<div class="report-toolbar">
  <button id="edit-report-btn" class="toolbar-btn">
    <i class="fas fa-edit"></i>
  </button>
  <button id="add-report-btn" class="toolbar-btn">
    <i class="fas fa-plus"></i>
  </button>
</div>
```

#### Edit Report Dropdown
- Displays list of available reports with timestamps
- Shows recent reports first (last 30 days)
- Includes report ID and creation date for identification

#### Report Form Modal
- Unified modal for both edit and create operations
- Dynamic field population based on operation type
- Real-time validation with visual feedback
- Responsive design for desktop and tablet

### 2. Backend API Endpoints

#### Update Report Endpoint
```
PUT /reports/update-report/<report_id>/
Content-Type: application/json
Authorization: Required (Moderator only)

Request Body:
{
  "systolic_blood_pressure": "120",
  "diastolic_blood_pressure": "80",
  "pulse": "72",
  "spo2": "98",
  "temperature": "98.6",
  "blood_glucose": "95",
  "symptoms": "Patient feeling well"
}
```

#### Create Report Endpoint (Enhanced)
```
POST /reports/create-report-manual/
Content-Type: application/json
Authorization: Required (Moderator only)

Request Body:
{
  "patient_id": "uuid",
  "systolic_blood_pressure": "120",
  "diastolic_blood_pressure": "80",
  "pulse": "72",
  "spo2": "98",
  "temperature": "98.6",
  "blood_glucose": "95",
  "symptoms": "Manual entry by moderator"
}
```

## Data Models

### Report Fields for Form
```javascript
const reportFields = {
  // Primary vital signs
  systolic_blood_pressure: { type: 'number', min: 70, max: 250, required: false },
  diastolic_blood_pressure: { type: 'number', min: 40, max: 150, required: false },
  pulse: { type: 'number', min: 30, max: 200, required: false },
  spo2: { type: 'number', min: 70, max: 100, required: false },
  temperature: { type: 'number', min: 95, max: 110, step: 0.1, required: false },
  blood_glucose: { type: 'number', min: 50, max: 500, required: false },
  
  // Additional fields
  symptoms: { type: 'textarea', maxLength: 500, required: false },
  measurement_timestamp: { type: 'datetime-local', required: false }
};
```

## Error Handling

### Client-Side Validation
- Real-time field validation with visual indicators
- Range checking for vital signs values
- Required field validation
- Format validation for numeric inputs

### Server-Side Validation
- Data type validation
- Business rule validation (e.g., reasonable vital signs ranges)
- Permission validation (moderator-only access)
- Database constraint validation

### Error Response Format
```json
{
  "success": false,
  "errors": {
    "systolic_blood_pressure": ["Value must be between 70 and 250"],
    "pulse": ["This field is required"]
  },
  "message": "Validation failed"
}
```

## Testing Strategy

### Unit Tests
- Form validation functions
- API endpoint functionality
- Data transformation utilities
- Permission checking logic

### Integration Tests
- End-to-end report creation workflow
- Edit report functionality
- Modal interaction behavior
- Table refresh after operations

### User Acceptance Tests
- Moderator can successfully edit existing reports
- Moderator can create new reports with valid data
- Form validation prevents invalid data submission
- UI provides clear feedback for all operations
- Mobile/tablet responsiveness works correctly

## Implementation Phases

### Phase 1: Backend API Development
1. Create update report endpoint
2. Enhance create report endpoint for manual entry
3. Add proper validation and error handling
4. Implement permission checks

### Phase 2: Frontend UI Development
1. Add toolbar icons to vitals table
2. Implement edit report dropdown
3. Create unified report form modal
4. Add client-side validation

### Phase 3: Integration and Testing
1. Connect frontend to backend APIs
2. Implement error handling and user feedback
3. Add loading states and success messages
4. Test responsive design

### Phase 4: Polish and Optimization
1. Add smooth animations and transitions
2. Optimize API calls and caching
3. Implement keyboard shortcuts
4. Add accessibility features