#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert raw patient data to FHIR format for the readmission prediction model.
"""

import os
import json
import uuid
import base64
import datetime
from pathlib import Path

# Set paths
DATA_DIR = Path("../data")
RAW_DIR = DATA_DIR / "raw"
FHIR_DIR = DATA_DIR / "fhir"

# Ensure output directory exists
FHIR_DIR.mkdir(exist_ok=True, parents=True)

def generate_id():
    """Generate a unique ID for FHIR resources."""
    return str(uuid.uuid4())

def create_patient_resource(patient_id):
    """Create a FHIR Patient resource."""
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
        },
        "identifier": [
            {
                "system": "http://hospital.example.org/identifiers/patients",
                "value": patient_id
            }
        ],
        "active": True,
        "name": [
            {
                "use": "official",
                "family": f"Patient{patient_id.upper()}"
            }
        ],
        "gender": "unknown",
        "birthDate": "1970-01-01"  # Default birthdate as actual data isn't available
    }

def create_encounter_resource(patient_id, vitals_data):
    """Create a FHIR Encounter resource from vitals data."""
    encounter_id = f"encounter-{patient_id}"
    
    # Calculate admission date from discharge date and length of stay
    discharge_date = vitals_data.get("discharge_date")
    length_of_stay = vitals_data.get("length_of_stay_days", 0)
    
    if discharge_date:
        discharge_datetime = datetime.datetime.fromisoformat(discharge_date)
        admission_datetime = discharge_datetime - datetime.timedelta(days=length_of_stay)
        admission_date = admission_datetime.date().isoformat()
    else:
        admission_date = "2023-01-01"  # Default if missing
        discharge_date = "2023-01-02"  # Default if missing
    
    encounter = {
        "resourceType": "Encounter",
        "id": encounter_id,
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter"]
        },
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
            "display": "inpatient encounter"
        },
        "type": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "185347001",
                        "display": "Encounter for problem"
                    }
                ]
            }
        ],
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "period": {
            "start": admission_date,
            "end": discharge_date
        },
        "length": {
            "value": length_of_stay,
            "unit": "days",
            "system": "http://unitsofmeasure.org",
            "code": "d"
        },
        "diagnosis": [],
        "hospitalization": {}
    }
    
    # Add ICU duration if available
    if "icu_duration_hours" in vitals_data:
        encounter["hospitalization"]["extension"] = [
            {
                "url": "http://example.org/fhir/StructureDefinition/icu-duration",
                "valueQuantity": {
                    "value": vitals_data["icu_duration_hours"],
                    "unit": "hours",
                    "system": "http://unitsofmeasure.org",
                    "code": "h"
                }
            }
        ]
    
    return encounter

def create_vital_sign_observations(patient_id, encounter_id, vital_signs):
    """Create FHIR Observation resources for vital signs."""
    observations = []
    
    for idx, vital in enumerate(vital_signs):
        timestamp = vital.get("timestamp", "2023-01-01")
        
        # Temperature observation
        if "temperature" in vital:
            temp_value = vital["temperature"].replace("F", "").strip()
            observations.append({
                "resourceType": "Observation",
                "id": f"temp-{patient_id}-{idx}",
                "meta": {
                    "profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]
                },
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8310-5",
                            "display": "Body temperature"
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "encounter": {
                    "reference": f"Encounter/{encounter_id}"
                },
                "effectiveDateTime": timestamp.replace(" ", "T"),
                "valueQuantity": {
                    "value": float(temp_value),
                    "unit": "°F",
                    "system": "http://unitsofmeasure.org",
                    "code": "[degF]"
                }
            })
        
        # Pulse rate observation
        if "pulse_rate" in vital:
            pulse_value = vital["pulse_rate"].replace("bpm", "").strip()
            observations.append({
                "resourceType": "Observation",
                "id": f"pulse-{patient_id}-{idx}",
                "meta": {
                    "profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]
                },
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8867-4",
                            "display": "Heart rate"
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "encounter": {
                    "reference": f"Encounter/{encounter_id}"
                },
                "effectiveDateTime": timestamp.replace(" ", "T"),
                "valueQuantity": {
                    "value": int(pulse_value),
                    "unit": "beats/minute",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min"
                }
            })
        
        # Blood pressure observation
        if "blood_pressure" in vital:
            bp_parts = vital["blood_pressure"].split("/")
            if len(bp_parts) == 2:
                systolic = int(bp_parts[0].strip())
                diastolic = int(bp_parts[1].strip())
                
                observations.append({
                    "resourceType": "Observation",
                    "id": f"bp-{patient_id}-{idx}",
                    "meta": {
                        "profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]
                    },
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                    "display": "Vital Signs"
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "85354-9",
                                "display": "Blood pressure panel"
                            }
                        ]
                    },
                    "subject": {
                        "reference": f"Patient/{patient_id}"
                    },
                    "encounter": {
                        "reference": f"Encounter/{encounter_id}"
                    },
                    "effectiveDateTime": timestamp.replace(" ", "T"),
                    "component": [
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "8480-6",
                                        "display": "Systolic blood pressure"
                                    }
                                ]
                            },
                            "valueQuantity": {
                                "value": systolic,
                                "unit": "mmHg",
                                "system": "http://unitsofmeasure.org",
                                "code": "mm[Hg]"
                            }
                        },
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "8462-4",
                                        "display": "Diastolic blood pressure"
                                    }
                                ]
                            },
                            "valueQuantity": {
                                "value": diastolic,
                                "unit": "mmHg",
                                "system": "http://unitsofmeasure.org",
                                "code": "mm[Hg]"
                            }
                        }
                    ]
                })
    
    return observations

def create_critical_event_observations(patient_id, encounter_id, critical_events):
    """Create FHIR Observation resources for critical events."""
    observations = []
    
    for idx, event in enumerate(critical_events):
        observations.append({
            "resourceType": "Observation",
            "id": f"event-{patient_id}-{idx}",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "exam",
                            "display": "Examination"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "404684003",  # Generic SNOMED code for clinical finding
                        "display": event.get("event", "Critical event")
                    }
                ],
                "text": event.get("event", "Critical event")
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "encounter": {
                "reference": f"Encounter/{encounter_id}"
            },
            "effectiveDateTime": event.get("timestamp", "2023-01-01").replace(" ", "T"),
            "valueString": event.get("event", "Critical event")
        })
    
    return observations

def create_procedure_resources(patient_id, encounter_id, surgical_interventions):
    """Create FHIR Procedure resources for surgical interventions."""
    procedures = []
    
    for idx, intervention in enumerate(surgical_interventions):
        procedures.append({
            "resourceType": "Procedure",
            "id": f"procedure-{patient_id}-{idx}",
            "status": "completed",
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "387713003",  # Generic SNOMED code for surgical procedure
                        "display": intervention.get("procedure", "Surgical procedure")
                    }
                ],
                "text": intervention.get("procedure", "Surgical procedure")
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "encounter": {
                "reference": f"Encounter/{encounter_id}"
            },
            "performedDateTime": intervention.get("timestamp", "2023-01-01")
        })
    
    return procedures

def create_condition_resources(patient_id, encounter_id, infection_records):
    """Create FHIR Condition resources for infection records."""
    conditions = []
    
    for idx, infection in enumerate(infection_records):
        onset_date = infection.get("onset_date", "2023-01-01")
        duration_days = infection.get("duration_days", 7)
        
        # Calculate abatement date
        onset_datetime = datetime.datetime.fromisoformat(onset_date)
        abatement_datetime = onset_datetime + datetime.timedelta(days=duration_days)
        abatement_date = abatement_datetime.date().isoformat()
        
        conditions.append({
            "resourceType": "Condition",
            "id": f"condition-{patient_id}-{idx}",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "resolved",
                        "display": "Resolved"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "problem-list-item",
                            "display": "Problem List Item"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "40733004",  # Generic SNOMED code for infection
                        "display": infection.get("infection_type", "Infection")
                    }
                ],
                "text": infection.get("infection_type", "Infection")
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "encounter": {
                "reference": f"Encounter/{encounter_id}"
            },
            "onsetDateTime": onset_date,
            "abatementDateTime": abatement_date
        })
    
    return conditions

def create_care_plan_resource(patient_id, encounter_id, followup_days):
    """Create a FHIR CarePlan resource for follow-up care."""
    if not followup_days:
        return None
    
    return {
        "resourceType": "CarePlan",
        "id": f"careplan-{patient_id}",
        "status": "active",
        "intent": "plan",
        "title": "Follow-up Care Plan",
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "encounter": {
            "reference": f"Encounter/{encounter_id}"
        },
        "period": {
            "start": datetime.datetime.now().date().isoformat()
        },
        "activity": [
            {
                "detail": {
                    "status": "scheduled",
                    "description": "Follow-up appointment",
                    "scheduledTiming": {
                        "repeat": {
                            "count": 1,
                            "duration": followup_days,
                            "durationUnit": "d"
                        }
                    }
                }
            }
        ]
    }

def create_document_reference(patient_id, encounter_id, clinical_notes):
    """Create a FHIR DocumentReference resource for clinical notes."""
    if not clinical_notes:
        return None
    
    # Base64 encode the notes
    encoded_notes = base64.b64encode(clinical_notes.encode('utf-8')).decode('utf-8')
    
    return {
        "resourceType": "DocumentReference",
        "id": f"docref-{patient_id}",
        "status": "current",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11488-4",
                    "display": "Consult note"
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "context": {
            "encounter": [
                {
                    "reference": f"Encounter/{encounter_id}"
                }
            ]
        },
        "date": datetime.datetime.now().isoformat(),
        "content": [
            {
                "attachment": {
                    "contentType": "text/plain",
                    "data": encoded_notes,
                    "title": f"Clinical Notes for Patient {patient_id}"
                }
            }
        ]
    }

def convert_patient_data_to_fhir(patient_id, clinical_notes, vitals_data):
    """Convert a patient's data to FHIR resources."""
    # Generate resources
    resources = []
    
    # Create Patient resource
    patient_resource = create_patient_resource(patient_id)
    resources.append(patient_resource)
    
    # Create Encounter resource
    encounter_resource = create_encounter_resource(patient_id, vitals_data)
    encounter_id = encounter_resource["id"]
    resources.append(encounter_resource)
    
    # Create Observation resources for vital signs
    if "vital_signs" in vitals_data:
        vital_sign_observations = create_vital_sign_observations(
            patient_id, encounter_id, vitals_data["vital_signs"]
        )
        resources.extend(vital_sign_observations)
    
    # Create Observation resources for critical events
    if "critical_events" in vitals_data:
        critical_event_observations = create_critical_event_observations(
            patient_id, encounter_id, vitals_data["critical_events"]
        )
        resources.extend(critical_event_observations)
    
    # Create Procedure resources
    if "surgical_interventions" in vitals_data:
        procedure_resources = create_procedure_resources(
            patient_id, encounter_id, vitals_data["surgical_interventions"]
        )
        resources.extend(procedure_resources)
    
    # Create Condition resources
    if "infection_records" in vitals_data:
        condition_resources = create_condition_resources(
            patient_id, encounter_id, vitals_data["infection_records"]
        )
        resources.extend(condition_resources)
    
    # Create CarePlan resource
    if "post_discharge_followup_time_days" in vitals_data:
        care_plan = create_care_plan_resource(
            patient_id, encounter_id, vitals_data["post_discharge_followup_time_days"]
        )
        if care_plan:
            resources.append(care_plan)
    
    # Create DocumentReference for clinical notes
    if clinical_notes:
        document_reference = create_document_reference(patient_id, encounter_id, clinical_notes)
        if document_reference:
            resources.append(document_reference)
    
    # Create bundle
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": resource
            } for resource in resources
        ]
    }
    
    return bundle

def process_all_patients():
    """Process all patient data in the raw directory."""
    # Get all patient text files
    txt_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.txt')]
    
    # Process each patient
    for txt_file in txt_files:
        # Extract patient_id from filename
        patient_id = txt_file.split('.')[0]  # patient_a_1
        
        # Read clinical notes
        with open(os.path.join(RAW_DIR, txt_file), 'r') as f:
            clinical_notes = f.read()
        
        # Find corresponding vitals file
        vitals_file = f"{patient_id}_vitals.json"
        vitals_path = os.path.join(RAW_DIR, vitals_file)
        
        if os.path.exists(vitals_path):
            with open(vitals_path, 'r') as f:
                vitals_data = json.load(f)
            
            # Convert to FHIR
            fhir_bundle = convert_patient_data_to_fhir(patient_id, clinical_notes, vitals_data)
            
            # Save FHIR bundle
            output_path = os.path.join(FHIR_DIR, f"{patient_id}.json")
            with open(output_path, 'w') as f:
                json.dump(fhir_bundle, f, indent=2)
            
            print(f"Converted {patient_id} to FHIR format: {output_path}")
        else:
            print(f"Warning: No vitals data found for {patient_id}")

if __name__ == "__main__":
    # Create scripts directory if it doesn't exist
    scripts_dir = Path("./")
    if not scripts_dir.is_dir():
        scripts_dir.mkdir(exist_ok=True)
    
    # Create data/fhir directory if it doesn't exist
    (DATA_DIR / "fhir").mkdir(exist_ok=True, parents=True)
    
    # Process all patients
    process_all_patients()
    
    print("\nConversion complete. FHIR resources are available in the data/fhir directory.")