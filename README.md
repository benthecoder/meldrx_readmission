# Head and Neck Cancer Readmission Prediction

## Project Overview

This application predicts the likelihood of readmission for head and neck cancer patients from diagnosis to first discharge. Using patient data including vital signs, critical events, and clinical notes, the model outputs a binary prediction (0/1) indicating readmission risk.

## Data Description

The system uses synthetic patient data that maps to FHIR resources as follows:

### FHIR Resource Mapping

1. **Encounter** - Contains hospitalization details

   - discharge_date → Encounter.period.end
   - length_of_stay_days → Encounter.length
   - icu_duration_hours → Encounter.hospitalization.extension

2. **Observation (Vital Signs)** - Multiple observations for each vital sign

   - timestamp → Observation.effectiveDateTime
   - temperature → Observation with LOINC code 8310-5
   - pulse_rate → Observation with LOINC code 8867-4
   - blood_pressure → Observation with LOINC code 85354-9 (with components)

3. **Observation (Clinical Events)** - For critical events

   - critical_events.event → Observation.code
   - critical_events.timestamp → Observation.effectiveDateTime

4. **Procedure** - For surgical interventions

   - surgical_interventions.procedure → Procedure.code
   - surgical_interventions.timestamp → Procedure.performedDateTime

5. **Condition** - For infection records

   - infection_records.infection_type → Condition.code
   - infection_records.onset_date → Condition.onsetDateTime
   - infection_records.duration_days → Used to calculate Condition.abatementDateTime

6. **CarePlan** - For follow-up planning

   - post_discharge_followup_time_days → CarePlan.activity.detail.scheduledTiming

7. **DiagnosticReport** - For MRI and imaging results

   - Contains Observation references and summary findings

8. **DocumentReference** - For clinical notes
   - text → DocumentReference.content.attachment.data

### Sample Data Structure (Original JSON)

```json
{
  "discharge_date": "2023-10-15",
  "length_of_stay_days": 10,
  "icu_duration_hours": 72,
  "critical_events": [
    {
      "event": "respiratory arrest",
      "timestamp": "2023-10-10 04:30"
    }
  ],
  "vital_signs": [
    {
      "timestamp": "2023-10-05 08:00",
      "temperature": "98.7F",
      "pulse_rate": "85 bpm",
      "blood_pressure": "130/75"
    }
  ],
  "post_discharge_followup_time_days": 14,
  "surgical_interventions": [
    {
      "procedure": "Coronary artery bypass grafting",
      "timestamp": "2023-10-05"
    }
  ],
  "infection_records": [
    {
      "infection_type": "Urinary tract infection",
      "onset_date": "2023-10-08",
      "duration_days": 5
    }
  ],
  "mri_notes": "MRI FINDINGS: T1 and T2-weighted images demonstrate a 2.8 x 3.1 cm heterogeneous mass in the right oropharynx extending to the base of tongue. The mass shows intermediate signal on T1 and hyperintense signal on T2 with areas of central necrosis. Post-contrast images reveal heterogeneous enhancement. Multiple enlarged right level II and III lymph nodes are present, largest measuring 1.7 cm with evidence of extracapsular extension. No evidence of perineural invasion or carotid artery encasement. No intracranial extension. IMPRESSION: Right oropharyngeal mass consistent with squamous cell carcinoma, stage T3N2b, with multiple ipsilateral lymph node involvement."
}
```

## Features

- **Model Input**: Summarized clinical notes and vital signs
- **Model Output**: Binary prediction (0/1) for readmission risk
- **Explainability**: SHAP (SHapley Additive exPlanations) values to interpret model decisions

## User Interface

The application provides a comprehensive view for each patient:

- Detailed patient information
- Summarized clinical notes
- Vital signs visualization
- Readmission prediction tab

## References

- [medical hack — How to Implement CDS Hooks into your FHIR App (ft. Anton Wieslander) - YouTube](https://www.youtube.com/watch?v=o2CCoSUMZEI)
- [medical hack — darena-solutions/yt-cds-hook-integration](https://github.com/darena-solutions/yt-cds-hook-integration)
- [medical hack — 2.0 - CDS Hooks](https://cds-hooks.hl7.org/2.0/)
