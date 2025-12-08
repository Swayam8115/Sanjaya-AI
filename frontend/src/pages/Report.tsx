import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate, useLocation } from "react-router-dom";
import { Download, ArrowLeft, FileText, TrendingUp, FlaskConical, Scale, Globe } from "lucide-react";
import { toast } from "sonner";

const Report = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const results = location.state?.results || {};

  const handleDownload = () => {
    if (results.REPORT && results.REPORT.output && results.REPORT.output.file_path) {
      const filePath = results.REPORT.output.file_path;
      // Extract filename from path (e.g. ./generated_reports/report_123.pdf -> report_123.pdf)
      const filename = filePath.split('/').pop() || "report.pdf";

      // Since we mounted /reports to generated_reports, we can construct the URL
      const downloadUrl = `http://localhost:8000/reports/${filename}`;

      // Trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename; // This attribute hints the browser to download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast.success(`✅ Downloading report: ${filename}`);
    } else {
      toast.error("❌ Report file path not found.");
    }
  };

  const iqvia = results.IQVIA?.output?.result || {};
  const clinicalReport = results.CLINICAL?.output || {};
  // Handle both old and new format tentatively, but prioritize new 'active_trials' structure
  const activeTrials = clinicalReport.active_trials || {};
  const sponsorProfiles = clinicalReport.sponsor_profiles || {};
  const phaseDistribution = clinicalReport.phase_distribution || {};

  const patents = results.PATENTS?.output?.data || [];
  const web = results.WEB?.output || {};
  const synth = results.SYNTHESIZED || {};


  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card shadow-sm h-24 flex items-center">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-primary" />
            <h1 className="text-2xl font-bold text-foreground">Research Report</h1>
          </div>
          <Button onClick={() => navigate("/")} variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Chat
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="mb-8 text-center animate-fade-in">
          <h2 className="text-3xl font-bold text-foreground mb-2">
            Drug Analysis
          </h2>
          <p className="text-muted-foreground mt-2">
            Generated on {new Date().toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric"
            })}
          </p>
        </div>

        <div className="space-y-6 animate-fade-in" style={{ animationDelay: "0.2s" }}>
          {/* Market Insights Card */}
          {results.IQVIA && (
            <Card className="p-6 shadow-lg">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center shrink-0">
                  <TrendingUp className="w-6 h-6 text-primary-foreground" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-3">Market Insights</h3>
                  {/* Dynamically render IQVIA data if available, else show raw output for now */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Array.isArray(iqvia) && iqvia.length > 0 ? (
                      iqvia.map((item: any, idx: number) => (
                        <div key={idx} className="bg-muted rounded-lg p-4">
                          <p className="text-sm text-muted-foreground">Region: {item.region}</p>
                          <p className="text-lg font-semibold text-foreground mt-1">Sales: {item.sales_value}</p>
                          <p className="text-sm text-success mt-1">Growth: {item.cagr || "N/A"}</p>
                        </div>
                      ))
                    ) : (
                      <div className="bg-muted rounded-lg p-4 col-span-3">
                        <p className="text-sm text-foreground">{JSON.stringify(iqvia).slice(0, 300)}...</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Clinical Trials Card */}
          {results.CLINICAL && (
            <div className="space-y-6">
              {/* Active Trials */}
              <Card className="p-6 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-lg bg-accent flex items-center justify-center shrink-0">
                    <FlaskConical className="w-6 h-6 text-accent-foreground" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-foreground mb-3">Clinical Trials</h3>
                    <div className="bg-muted rounded-lg p-4 mb-3">
                      <p className="text-sm text-muted-foreground mb-2">
                        Active Trials Found: <span className="font-semibold text-foreground">{activeTrials.total_found || 0}</span>
                        {activeTrials.condition_searched && <span> for condition: {activeTrials.condition_searched}</span>}
                      </p>
                      <div className="space-y-3">
                        {activeTrials.trials?.slice(0, 5).map((trial: any, idx: number) => (
                          <div key={idx} className="p-3 bg-background rounded-md border border-border">
                            <div className="flex justify-between items-start mb-1">
                              <a href={trial.trial_url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-primary hover:underline block truncate max-w-[70%]">
                                {trial.nct_id} - {trial.title}
                              </a>
                              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">{trial.phase}</span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                              <span>Sponsor: {trial.sponsor}</span>
                              <span>Status: {trial.status}</span>
                              <span>Enrollment: {trial.enrollment || "N/A"}</span>
                              <span>Locations: {trial.locations_count || 0}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    {activeTrials.view_all_url && (
                      <a href={activeTrials.view_all_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                        View All on ClinicalTrials.gov
                      </a>
                    )}
                  </div>
                </div>
              </Card>

              {/* Sponsor Profiles */}
              {sponsorProfiles.sponsors && sponsorProfiles.sponsors.length > 0 && (
                <Card className="p-6 shadow-lg">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-indigo-500 flex items-center justify-center shrink-0">
                      <TrendingUp className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-foreground mb-3">Top Sponsors</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {sponsorProfiles.sponsors.slice(0, 6).map((sponsor: any, idx: number) => (
                          <div key={idx} className="bg-muted rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-medium text-sm truncate pr-2" title={sponsor.sponsor_name}>{sponsor.sponsor_name}</h4>
                              <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">{sponsor.number_of_trials} Trials</span>
                            </div>
                            <p className="text-xs text-muted-foreground mb-1">Class: {sponsor.sponsor_class}</p>
                            <p className="text-xs text-muted-foreground">Phases: {sponsor.phases_involved?.join(", ")}</p>
                            {sponsor.sponsor_trials_url && (
                              <a href={sponsor.sponsor_trials_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline mt-2 inline-block">
                                View Trials
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              )}

              {/* Phase Distribution */}
              {phaseDistribution.distributions && phaseDistribution.distributions.length > 0 && (
                <Card className="p-6 shadow-lg">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-emerald-500 flex items-center justify-center shrink-0">
                      <Scale className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-foreground mb-3">Trial Phase Distribution</h3>
                      <div className="space-y-4">
                        {phaseDistribution.distributions.map((dist: any, idx: number) => (
                          <div key={idx} className="bg-muted rounded-lg p-3">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-medium text-sm">{dist.phase}</span>
                              <span className="text-sm font-bold">{dist.percentage?.toFixed(1)}% ({dist.number_of_trials})</span>
                            </div>
                            <div className="w-full bg-background rounded-full h-2 mb-2">
                              <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${dist.percentage}%` }}></div>
                            </div>
                            <p className="text-xs text-muted-foreground">Top Sponsors: {dist.top_sponsors?.slice(0, 3).join(", ")}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* Patent Landscape Card */}
          {results.PATENTS && (
            <Card className="p-6 shadow-lg">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shrink-0">
                  <Scale className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-3">Patent Landscape</h3>
                  <div className="bg-muted rounded-lg p-4">
                    {Array.isArray(patents) && patents.length > 0 ? (
                      <ul className="space-y-2">
                        {patents.map((p: any, idx: number) => (
                          <li key={idx} className="text-sm text-foreground">
                            <span className="font-bold">{p.patent_number}</span>: {p.title} (Expires: {p.expiration_date})
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground">No active patents found or data unavailable.</p>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Web Intelligence Card */}
          {results.WEB && (
            <Card className="p-6 shadow-lg">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center shrink-0">
                  <Globe className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-3">Web Intelligence</h3>
                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-sm text-foreground mb-3 font-medium">
                      key Insight: {web.summary?.summary?.[0] || "Analysis available."}
                    </p>
                    {web.summary?.quotes?.length > 0 && (
                      <div className="mt-2">
                        <p className="text-sm font-semibold mb-1">Top Quote:</p>
                        <p className="text-sm italic text-muted-foreground">"{web.summary.quotes[0].text}" - {web.summary.quotes[0].context}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Executive Summary Card */}
          {results.SYNTHESIZED && (
            <Card className="p-6 shadow-lg bg-gradient-to-br from-primary/5 to-secondary/5 border-primary/20">
              <h3 className="text-lg font-semibold text-foreground mb-3">Executive Summary</h3>
              <div className="text-foreground leading-relaxed prose prose-sm max-w-none">
                <p>{synth.final_summary}</p>
              </div>
              {synth.recommendations && (
                <div className="mt-4 p-4 bg-card rounded-lg border border-primary/20">
                  <p className="text-sm font-semibold text-primary mb-2">Recommendations:</p>
                  <p className="text-sm text-foreground whitespace-pre-wrap">{synth.recommendations}</p>
                </div>
              )}
            </Card>
          )}
        </div>

        <div className="mt-8 flex justify-center gap-4 animate-fade-in" style={{ animationDelay: "0.4s" }}>
          <Button onClick={handleDownload} size="lg" className="gap-2">
            <Download className="w-5 h-5" />
            Download PDF Report
          </Button>
          <Button onClick={() => navigate("/")} variant="outline" size="lg" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Chat
          </Button>
        </div>
      </main>
    </div>
  );
};

export default Report;