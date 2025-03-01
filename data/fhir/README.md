# FHIR Data

This directory contains patient data converted to FHIR format according to the mapping specified in the project's README.md.

## Format
Each file is a FHIR Bundle containing the following resources for a patient:

1. **Patient** - Basic patient information
2. **Encounter** - Hospitalization details with length of stay and ICU duration
3. **Observation (Vital Signs)** - Multiple observations for temperature, pulse rate, and blood pressure
4. **Observation (Clinical Events)** - For critical events during hospitalization
5. **Procedure** - For surgical interventions
6. **Condition** - For infection records
7. **CarePlan** - For follow-up planning
8. **DocumentReference** - For clinical notes (Base64 encoded)

## Readmission Status
The filename indicates the readmission status:
- Files ending with `_1.json` are patients who were readmitted (positive cases)
- Files ending with `_0.json` are patients who were not readmitted (negative cases)

## Usage
These files are ready to be used for model training and prediction. The model will analyze this FHIR data to predict readmission risk.