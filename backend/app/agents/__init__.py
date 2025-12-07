from .iqvia_agent import IQVIAAgent
# from .exim_agent import EXIMAgent
from .patent_agent import PatentLandscapeAgent
from .clinical_trials_agent import ClinicalTrialsAgent
from .internal_knowledge_agent import InternalKnowledgeAgent
from .web_intel_agent import WebIntelligenceAgent
from .report_generator_agent import ReportGeneratorAgent

iqvia_agent = IQVIAAgent()
# exim_agent = EXIMAgent()
patents_agent = PatentLandscapeAgent()
clinical_agent = ClinicalTrialsAgent()
internal_agent = InternalKnowledgeAgent()
web_agent = WebIntelligenceAgent()
report_agent = ReportGeneratorAgent()

__all__ = [
    "iqvia_agent",
    "exim_agent",
    "patents_agent",
    "clinical_agent",
    "internal_agent",
    "web_agent",
    "report_agent"
]
