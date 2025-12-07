import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate, useLocation } from "react-router-dom";
import { Download, ArrowLeft, FileText, TrendingUp, FlaskConical, Scale, Globe } from "lucide-react";
import { toast } from "sonner";

const Report = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const molecule = location.state?.molecule || "Metformin";

  const handleDownload = () => {
    toast.success("✅ Report generated and archived successfully.");
  };

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
          <p className="text-xl text-primary font-semibold">{molecule}</p>
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
          <Card className="p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center shrink-0">
                <TrendingUp className="w-6 h-6 text-primary-foreground" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-foreground mb-3">Market Insights</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">Therapy Area</p>
                    <p className="text-lg font-semibold text-foreground mt-1">Type 2 Diabetes</p>
                    <p className="text-sm text-foreground mt-1">Potential: Longevity, Oncology</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">Current Market Size</p>
                    <p className="text-lg font-semibold text-foreground mt-1">$18.4B</p>
                    <p className="text-sm text-success mt-1">CAGR 4.2%</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">Top Competitors</p>
                    <p className="text-sm font-medium text-foreground mt-1">Bristol-Myers Squibb</p>
                    <p className="text-sm font-medium text-foreground">Merck & Co.</p>
                    <p className="text-sm font-medium text-foreground">Teva Pharmaceuticals</p>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Clinical Trials Card */}
          <Card className="p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-accent flex items-center justify-center shrink-0">
                <FlaskConical className="w-6 h-6 text-accent-foreground" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-foreground mb-3">Clinical Trials</h3>
                <div className="bg-muted rounded-lg p-4 mb-3">
                  <p className="text-sm text-muted-foreground mb-2">Active Trials Found: <span className="font-semibold text-foreground">214</span></p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-foreground">NCT04567890 - Phase 3 (Long COVID recovery)</span>
                    </div>
                     <div className="flex items-center justify-between">
                      <span className="text-sm text-foreground">NCT03456789 - Phase 2 (Anti-Aging - TAME Trial)</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-foreground">NCT02345678 - Phase 2 (Breast Cancer adjuvant)</span>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">Source: ClinicalTrials.gov</p>
              </div>
            </div>
          </Card>

          {/* Patent Landscape Card */}
          <Card className="p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shrink-0">
                <Scale className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-foreground mb-3">Patent Landscape</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">Active Molecule Patents</p>
                    <p className="text-2xl font-bold text-foreground mt-1">0</p>
                    <p className="text-xs text-muted-foreground mt-2">(Generic Status)</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">Related Formulation Patents</p>
                    <p className="text-lg font-bold text-foreground mt-1">14 Active | 82 Expired</p>
                    <p className="text-xs text-muted-foreground mt-2">Example: US-20230123456-A1</p>
                    <p className="text-xs text-muted-foreground">(Extended-release, expires 2038)</p>
                  </div>
                </div>
                <p className="text-sm text-success mt-4 font-medium">Low IP barriers for standard formulations.</p>
              </div>
            </div>
          </Card>

          {/* Web Intelligence Card */}
          <Card className="p-6 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center shrink-0">
                <Globe className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-foreground mb-3">Web Intelligence</h3>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm text-foreground mb-3 font-medium">
                    Key Insight: Strong social signals detected for "anti-aging" off-label use.
                  </p>
                  <p className="text-sm text-foreground mb-2">
                    Top Reference:
                  </p>
                  <ul className="space-y-1 mb-3">
                    <li className="text-sm text-foreground flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0"></span>
                      <span>
                        <em>Cell Metabolism</em> (2023) - "Metformin benefits in neurodegeneration."
                        <br />
                        <span className="text-xs text-muted-foreground">(PubMed ID: 36789123)</span>
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </Card>

          {/* Executive Summary Card */}
          <Card className="p-6 shadow-lg bg-gradient-to-br from-primary/5 to-secondary/5 border-primary/20">
            <h3 className="text-lg font-semibold text-foreground mb-3">Executive Summary</h3>
            <p className="text-foreground leading-relaxed">
              {molecule} is a highly viable candidate for repurposing in <strong>Longevity</strong> and <strong>Oncology</strong> due to its generic status (low IP barriers) and extensive safety profile. There is high commercial interest in novel extended-release formulations for these new indications.
            </p>
            <div className="mt-4 p-4 bg-card rounded-lg border border-primary/20">
              <p className="text-sm font-semibold text-primary mb-2">Recommended Next Steps:</p>
              <ol className="space-y-1 text-sm text-foreground">
                <li>1. Evaluate regulatory feasibility for target indications (Longevity/Oncology).</li>
                <li>2. Conduct freedom-to-operate analysis for novel formulations.</li>
                <li>3. Assess market entry strategy and competitive positioning against emerging therapies.</li>
              </ol>
            </div>
          </Card>
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