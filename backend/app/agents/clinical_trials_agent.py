import requests
import json
import urllib.parse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
from app.utils.prompts import CLINICAL_TRIAL_SYSTEM_PROMPT
from app.tools.fetch_clinical_trial_data import execute_fetch_clinical_trials
from app.config.settings import settings
print(settings.GOOGLE_API_KEY)
client = OpenAI(
    api_key=settings.GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class ActiveTrial(BaseModel):
    """Detailed active clinical trial with links"""
    nct_id: str
    title: str
    sponsor: str
    sponsor_class: str
    phase: str
    status: str
    enrollment: Optional[int] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    study_type: Optional[str] = None
    locations_count: Optional[int] = None
    primary_outcome: Optional[str] = None
    trial_url: str
    sponsor_url: str

class ActiveTrialsTable(BaseModel):
    """Table of active clinical trials with search context"""
    total_found: int
    condition_searched: str
    trials: List[ActiveTrial]
    view_all_url: str

class SponsorProfile(BaseModel):
    """Detailed sponsor profile with trial analytics"""
    sponsor_name: str
    number_of_trials: int
    sponsor_class: str
    phases_involved: List[str]
    avg_enrollment: Optional[float] = None
    sponsor_trials_url: str
    sponsor_condition_url: str

class SponsorProfilesTable(BaseModel):
    """Table of sponsor profiles"""
    total_sponsors: int
    sponsors: List[SponsorProfile]

class PhaseDistribution(BaseModel):
    """Phase distribution with detailed insights"""
    phase: str
    number_of_trials: int
    percentage: float
    avg_enrollment: Optional[float] = None
    top_sponsors: List[str]
    phase_trials_url: str

class PhaseDistributionTable(BaseModel):
    """Table of trial phase distributions"""
    distributions: List[PhaseDistribution]

class ClinicalTrialsReport(BaseModel):
    """Complete enhanced report with all three tables and metadata"""
    report_generated_at: str
    search_query: str
    active_trials: ActiveTrialsTable
    sponsor_profiles: SponsorProfilesTable
    phase_distribution: PhaseDistributionTable


tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_clinical_trials",
            "description": "Fetch clinical trials data from ClinicalTrials.gov API. Use this to retrieve active trials for a given condition or query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "The disease, condition, or keyword to search for in trial conditions (e.g., 'cancer', 'diabetes')."
                    },
                    "status": {
                        "type": "string",
                        "default": "RECRUITING",
                        "description": "Trial status filter (e.g., 'RECRUITING' for actively recruiting, or 'ACTIVE_NOT_RECRUITING' for broadly active trials)."
                    },
                    "phase": {
                        "type": "string",
                        "description": "Optional phase filter (e.g., 'PHASE2', 'PHASE3')."
                    },
                    "page_size": {
                        "type": "integer",
                        "default": 10,
                        "description": "Number of results to fetch (max 1000)."
                    }
                },
                "required": ["condition"]
            }
        }
    }
]

def execute_tool(tool_call: Any) -> str:
    """Execute the tool based on the tool call."""
    if tool_call.function.name == "fetch_clinical_trials":
        try:
            args = json.loads(tool_call.function.arguments)
            return execute_fetch_clinical_trials(args)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Failed to parse tool arguments: {str(e)}"})
    else:
        return json.dumps({"error": "Unknown tool"})


def run_clinical_trials_agent(user_query: str) -> ClinicalTrialsReport:
    """
    Run the agent conversation loop with enhanced structured output.
    Returns a detailed ClinicalTrialsReport object with links and metadata.
    """
    
    messages = [
        {"role": "system", "content": CLINICAL_TRIAL_SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]

    max_iterations = 5
    iteration = 0
    while iteration < max_iterations:
        try:
            response = client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1
            )
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            raise

        choice = response.choices[0]
        message = choice.message

        if message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            })
            
            # Execute tools
            for tool_call in message.tool_calls:
                tool_result = execute_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                    "name": tool_call.function.name
                })
            iteration += 1
        else:
            break

    messages.append({
        "role": "user",
        "content": f"""Based on the clinical trials data you fetched, provide a comprehensive structured report.
            Include:
            - All trial details (enrollment, dates, locations, outcomes)
            - Direct links for each trial (trial_url, sponsor_url)
            - Sponsor analytics (phases involved, average enrollment)
            - Phase distribution with percentages and top sponsors
            - Properly formatted and URL-encoded links

            Current timestamp: {datetime.now().isoformat()}
            Original query: {user_query}

            Generate the complete ClinicalTrialsReport now."""
        })

    try:
        structured_response = client.beta.chat.completions.parse(
            model="gemini-2.5-flash",
            messages=messages,
            response_format=ClinicalTrialsReport,
            temperature=0.1
        )
        
        return structured_response.choices[0].message.parsed
    except Exception as e:
        print(f"Error getting structured output: {str(e)}")
        raise

def display_report(report: ClinicalTrialsReport):
    """Display the enhanced structured report with clickable links"""
    
    print("\n" + "="*120)
    print("CLINICAL TRIALS COMPREHENSIVE ANALYSIS REPORT")
    print("="*120)
    print(f"Generated: {report.report_generated_at}")
    print(f"Search Query: {report.search_query}")
    print(f"View All Results: {report.active_trials.view_all_url}")
    
    # Active Trials Table
    print(f"\n\nACTIVE TRIALS (Total Found: {report.active_trials.total_found}, Condition: {report.active_trials.condition_searched})")
    print("-"*120)
    print(f"{'NCT ID':<15} {'Title':<35} {'Sponsor':<20} {'Phase':<12} {'Enrollment':<12} {'Locations':<10}")
    print("-"*120)
    for trial in report.active_trials.trials[:10]:
        title_short = (trial.title[:32] + '...') if len(trial.title) > 35 else trial.title
        sponsor_short = (trial.sponsor[:17] + '...') if len(trial.sponsor) > 20 else trial.sponsor
        enrollment_str = str(trial.enrollment) if trial.enrollment else "N/A"
        locations_str = str(trial.locations_count) if trial.locations_count else "N/A"
        print(f"{trial.nct_id:<15} {title_short:<35} {sponsor_short:<20} {trial.phase:<12} {enrollment_str:<12} {locations_str:<10}")
        print(f"Trial: {trial.trial_url}")
        print(f"Start: {trial.start_date} | Complete: {trial.completion_date} | Type: {trial.study_type}")
        if trial.primary_outcome and trial.primary_outcome != "Not Specified":
            outcome_short = (trial.primary_outcome[:80] + '...') if len(trial.primary_outcome) > 80 else trial.primary_outcome
            print(f"Primary Outcome: {outcome_short}")
        print()
    
    # Sponsor Profiles Table
    print(f"\n\nSPONSOR PROFILES (Total Sponsors: {report.sponsor_profiles.total_sponsors})")
    print("-"*120)
    print(f"{'Sponsor Name':<40} {'Trials':<10} {'Class':<15} {'Phases':<25} {'Avg Enroll':<12}")
    print("-"*120)
    for sponsor in sorted(report.sponsor_profiles.sponsors, key=lambda x: x.number_of_trials, reverse=True)[:15]:
        sponsor_name_short = (sponsor.sponsor_name[:37] + '...') if len(sponsor.sponsor_name) > 40 else sponsor.sponsor_name
        phases_str = ", ".join(sponsor.phases_involved[:3]) if sponsor.phases_involved else "N/A"
        avg_enroll = f"{sponsor.avg_enrollment:.0f}" if sponsor.avg_enrollment else "N/A"
        print(f"{sponsor_name_short:<40} {sponsor.number_of_trials:<10} {sponsor.sponsor_class:<15} {phases_str:<25} {avg_enroll:<12}")
        print(f"All Trials: {sponsor.sponsor_trials_url}")
        print(f"Condition Trials: {sponsor.sponsor_condition_url}")
        print()
    
    # Phase Distribution Table
    print(f"\n\nTRIAL PHASE DISTRIBUTION")
    print("-"*120)
    print(f"{'Phase':<20} {'Trials':<10} {'Percentage':<15} {'Avg Enroll':<15} {'Top Sponsors':<50}")
    print("-"*120)
    for phase in sorted(report.phase_distribution.distributions, key=lambda x: x.number_of_trials, reverse=True):
        top_sponsors_str = ", ".join(phase.top_sponsors[:3]) if phase.top_sponsors else "N/A"
        avg_enroll = f"{phase.avg_enrollment:.0f}" if phase.avg_enrollment else "N/A"
        print(f"{phase.phase:<20} {phase.number_of_trials:<10} {phase.percentage:<15.1f}% {avg_enroll:<15} {top_sponsors_str:<50}")
        print(f"View Phase Trials: {phase.phase_trials_url}")
        print()
    
    print("\n" + "="*120 + "\n")

# ==================== Main Execution ====================

if __name__ == "__main__":
    query = 'Show me active clinical trials for breast cancer, including sponsor profiles and phase distributions.'
    try:
        report = run_clinical_trials_agent(query)
        display_report(report)       
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()