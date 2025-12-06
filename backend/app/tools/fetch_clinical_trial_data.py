import requests
import json
from typing import Dict, Any

def execute_fetch_clinical_trials(args: Dict[str, Any]) -> str:
    """
    Execute the fetch_clinical_trials tool by calling the ClinicalTrials.gov API v2.
    Returns a JSON string with enhanced study data including enrollment, dates, locations.
    """
    url = "https://clinicaltrials.gov/api/v2/studies" #ClinicalTrials.gov 
    params = {
        "query.cond": args.get("condition"),
        "filter.overallStatus": args.get("status", "RECRUITING"),
        "pageSize": 5,
        "format": "json",
        "countTotal": "true"
    }
    
    if args.get("phase"):
        phase = args["phase"].replace("_", "")
        params["filter.phase"] = phase

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"API request failed: {str(e)}"})

    try:
        data = response.json()
    except json.JSONDecodeError:
        return json.dumps({"error": "Failed to parse API response"})

    studies = data.get("studies", [])
    total = data.get("totalCount", 0)

    # Enhanced data extraction with more details
    enhanced_studies = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        arms_module = protocol.get("armsInterventionsModule", {})
        sponsor_collab = protocol.get("sponsorCollaboratorsModule", {})
        outcomes_module = protocol.get("outcomesModule", {})
        eligibility_module = protocol.get("eligibilityModule", {})
        contacts_locations = protocol.get("contactsLocationsModule", {})
        
        lead_sponsor = sponsor_collab.get("leadSponsor", {})
        phases_list = design.get("phases", [])
        phase_str = ", ".join(phases_list) if phases_list else "Not Specified"
        
        conditions_list = conditions_module.get("conditions", [])
        conditions_str = ", ".join(conditions_list) if conditions_list else "Not Specified"
        
        interventions_list = arms_module.get("interventions", [])
        interventions_str = ", ".join([i.get("name", "") for i in interventions_list]) if interventions_list else "Not Specified"
        
        # Extract enrollment
        enrollment = design.get("enrollmentInfo", {}).get("count")
        
        # Extract dates
        start_date_struct = status_module.get("startDateStruct", {})
        start_date = start_date_struct.get("date", "Not Available")
        
        completion_date_struct = status_module.get("completionDateStruct", {}) or status_module.get("primaryCompletionDateStruct", {})
        completion_date = completion_date_struct.get("date", "Not Available")
        
        # Extract study type
        study_type = design.get("studyType", "Not Specified")
        
        # Extract primary outcome
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])
        primary_outcome = primary_outcomes[0].get("measure", "Not Specified") if primary_outcomes else "Not Specified"
        
        # Count locations
        locations = contacts_locations.get("locations", [])
        locations_count = len(locations)

        enhanced = {
            "nct_id": identification.get("nctId", ""),
            "brief_title": identification.get("briefTitle", ""),
            "overall_status": status_module.get("overallStatus", ""),
            "phase": phase_str,
            "lead_sponsor_name": lead_sponsor.get("name", ""),
            "sponsor_class": lead_sponsor.get("class", ""),
            "conditions": conditions_str,
            "interventions": interventions_str,
            "enrollment": enrollment,
            "start_date": start_date,
            "completion_date": completion_date,
            "study_type": study_type,
            "primary_outcome": primary_outcome,
            "locations_count": locations_count
        }
        enhanced_studies.append(enhanced)
    print(json.dumps({
        "total_studies": total,
        "fetched_count": len(enhanced_studies),
        "search_condition": args.get("condition"),
        "studies": enhanced_studies
    }, indent=2))
    return json.dumps({
        "total_studies": total,
        "fetched_count": len(enhanced_studies),
        "search_condition": args.get("condition"),
        "studies": enhanced_studies
    }, indent=2)
