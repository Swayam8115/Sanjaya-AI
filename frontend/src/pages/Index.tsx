import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";
import AgentMessage from "@/components/AgentMessage";
import ProgressTracker from "@/components/ProgressTracker";
import sanjayaLogo from "@/assets/sanjaya-logo.png";

interface Message {
  id: string;
  role: "user" | "master" | "market" | "trials" | "patent" | "web";
  content: string;
  agentName?: string;
}

interface Task {
  id: string;
  label: string;
  emoji: string;
  status: "pending" | "loading" | "complete";
}

const Index = () => {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTypingId, setCurrentTypingId] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);
  const [molecule, setMolecule] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, tasks]);

  const simulateAgentWorkflow = async (moleculeName: string) => {
    setIsProcessing(true);
    setMolecule(moleculeName);
    setProgress(0);
    setShowReport(false);

    // Initial tasks setup
    const initialTasks: Task[] = [
      { id: "market", label: "Market Data", emoji: "📊", status: "pending" },
      { id: "trials", label: "Clinical Trials", emoji: "🧬", status: "pending" },
      { id: "patent", label: "Patent Landscape", emoji: "📜", status: "pending" },
      { id: "web", label: "Web Intelligence", emoji: "🌐", status: "pending" },
      { id: "report", label: "Report Generation", emoji: "🧾", status: "pending" },
    ];
    setTasks(initialTasks);

    // Master Agent acknowledgment
    await new Promise(resolve => setTimeout(resolve, 500));
    const masterId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: masterId,
      role: "master",
      content: "Understood. Breaking down your request into modular research tasks...",
    }]);
    setCurrentTypingId(masterId);

    await new Promise(resolve => setTimeout(resolve, 2500));
    setCurrentTypingId(null);

    // Worker Agent 1: Market Data
    await new Promise(resolve => setTimeout(resolve, 800));
    setTasks(prev => prev.map(t => t.id === "market" ? { ...t, status: "loading" } : t));
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const marketId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: marketId,
      role: "market",
      content: `✅ Task complete (Progress: 20%)\n\nTherapy Area: Type 2 Diabetes Mellitus\nCurrent Market Size: $18.4B (CAGR 4.2%)\nTop Competitors: Bristol-Myers Squibb, Merck & Co., Teva Pharmaceuticals.`,
    }]);
    setCurrentTypingId(marketId);
    setTasks(prev => prev.map(t => t.id === "market" ? { ...t, status: "complete" } : t));
    setProgress(20);

    await new Promise(resolve => setTimeout(resolve, 2500));
    setCurrentTypingId(null);

    // Worker Agent 2: Clinical Trials
    await new Promise(resolve => setTimeout(resolve, 800));
    setTasks(prev => prev.map(t => t.id === "trials" ? { ...t, status: "loading" } : t));
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const trialsId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: trialsId,
      role: "trials",
      content: `✅ Task complete (Progress: 40%)\n\nFound 214 active trials for ${moleculeName} repurposing.\nKey Trials Identified:\n- NCT04567890 (Phase 3 - Long COVID)\n- NCT03456789 (Phase 2 - Anti-Aging TAME Trial)\n- NCT02345678 (Phase 2 - Breast Cancer adjuvant)`,
    }]);
    setCurrentTypingId(trialsId);
    setTasks(prev => prev.map(t => t.id === "trials" ? { ...t, status: "complete" } : t));
    setProgress(40);

    await new Promise(resolve => setTimeout(resolve, 2500));
    setCurrentTypingId(null);

    // Worker Agent 3: Patent Landscape
    await new Promise(resolve => setTimeout(resolve, 800));
    setTasks(prev => prev.map(t => t.id === "patent" ? { ...t, status: "loading" } : t));
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const patentId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: patentId,
      role: "patent",
      content: `✅ Task complete (Progress: 60%)\n\nActive Molecule Patents: 0 (Generic status)\nRelated Formulation Patents: 14 Active | 82 Expired\nExample: US-20230123456-A1 (Extended-release, expires 2038)`,
    }]);
    setCurrentTypingId(patentId);
    setTasks(prev => prev.map(t => t.id === "patent" ? { ...t, status: "complete" } : t));
    setProgress(60);

    await new Promise(resolve => setTimeout(resolve, 2500));
    setCurrentTypingId(null);

    // Worker Agent 4: Web Intelligence
    await new Promise(resolve => setTimeout(resolve, 800));
    setTasks(prev => prev.map(t => t.id === "web" ? { ...t, status: "loading" } : t));
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const webId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: webId,
      role: "web",
      content: `✅ Task complete (Progress: 80%)\n\nKey Insight: Strong social signals detected for "anti-aging" off-label use.\nTop Reference: Cell Metabolism (2023) - "Metformin benefits in neurodegeneration." (PubMed ID: 36789123)`,
    }]);
    setCurrentTypingId(webId);
    setTasks(prev => prev.map(t => t.id === "web" ? { ...t, status: "complete" } : t));
    setProgress(80);

    await new Promise(resolve => setTimeout(resolve, 2500));
    setCurrentTypingId(null);

    // Final synthesis
    await new Promise(resolve => setTimeout(resolve, 800));
    setTasks(prev => prev.map(t => t.id === "report" ? { ...t, status: "loading" } : t));
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const summaryId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: summaryId,
      role: "master",
      content: `✅ Analysis Complete (Progress: 100%)\n\n${moleculeName} is a highly viable candidate for repurposing in Longevity and Oncology due to generic status and extensive safety profile.\n\nHigh commercial interest in novel extended-release formulations for these new indications.`,
    }]);
    setCurrentTypingId(summaryId);
    setTasks(prev => prev.map(t => t.id === "report" ? { ...t, status: "complete" } : t));
    setProgress(100);

    await new Promise(resolve => setTimeout(resolve, 2500));
    setCurrentTypingId(null);
    setShowReport(true);
    setIsProcessing(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Extract molecule name from input, default to "Metformin" if not found for demo purposes
    // This simple regex looks for a word after "molecule" or just takes the last word if it looks like a drug name.
    let moleculeName = "Metformin";
    const moleculeMatch = input.match(/(?:molecule|drug)\s+(\w+)/i);
    if (moleculeMatch) {
        moleculeName = moleculeMatch[1];
    } else {
        //fallback: try to find a capitalized word that might be a drug name if the input is short
        const words = input.trim().split(' ');
        if (words.length <= 3) {
             const potentialDrug = words.find(w => /^[A-Z][a-z]+$/.test(w));
             if (potentialDrug) moleculeName = potentialDrug;
        }
    }
    // Capitalize first letter for consistency
    moleculeName = moleculeName.charAt(0).toUpperCase() + moleculeName.slice(1);

    setInput("");
    await simulateAgentWorkflow(moleculeName);
  };

  const handleGenerateReport = () => {
    navigate("/report", { state: { molecule } });
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card shadow-sm h-24 flex items-center">
        <div className="container mx-auto px-4 flex items-center">
          <div className="flex items-center gap-3">
            <img src={sanjayaLogo} alt="Sanjaya Logo" className="w-25 h-24 object-contain" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">Sanjaya</h1>
              <p className="text-sm text-muted-foreground">AI-Powered Pharma Intelligence</p>
            </div>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 py-6 max-w-4xl">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
              <img src={sanjayaLogo} alt="Sanjaya Logo" className="w-40 h-40 object-contain" />
              <h2 className="text-3xl font-bold text-foreground mb-3">
                Welcome to Sanjaya
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl">
                Discover drug repurposing opportunities powered by Sanjaya AI analyzing market data, 
                clinical trials, patents, and scientific literature.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <AgentMessage
              key={message.id}
              role={message.role}
              content={message.content}
              agentName={message.agentName}
              isTyping={currentTypingId === message.id}
              onTypingComplete={() => setCurrentTypingId(null)}
            />
          ))}

          {tasks.length > 0 && (
            <div className="mb-4">
              <ProgressTracker tasks={tasks} progress={progress} />
            </div>
          )}

          {showReport && (
            <div className="flex justify-center animate-fade-in">
              <Button onClick={handleGenerateReport} size="lg" className="gap-2 shadow-lg">
                <FileText className="w-5 h-5" />
                Generate Report
              </Button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t bg-card shadow-lg">
        <div className="container mx-auto px-4 py-4 max-w-4xl">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about drug repurposing opportunities..."
              disabled={isProcessing}
              className="flex-1 bg-background"
            />
            <Button type="submit" disabled={isProcessing || !input.trim()} size="lg">
              <Send className="w-5 h-5" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Index;