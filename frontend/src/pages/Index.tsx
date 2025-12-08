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

  const handleApiWorkflow = async (moleculeName: string) => {
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

    try {
      // Master Agent acknowledgment
      const masterId = Date.now().toString();
      setMessages(prev => [...prev, {
        id: masterId,
        role: "master",
        content: "Understood. Orchestrating agents to research your query...",
      }]);

      // Start "loading" all tasks to show activity
      setTasks(prev => prev.map(t => ({ ...t, status: "loading" })));
      setProgress(20);

      // Call Backend API
      const data = await import("../api").then(m => m.sendMessage(input));

      // Process results sequentially for visual effect (optional, or just show all)
      // For now, let's mark all as done and update progress

      // 1. Market Data
      if (data.results.IQVIA) {
        setTasks(prev => prev.map(t => t.id === "market" ? { ...t, status: "complete" } : t));
        const marketId = Date.now().toString() + "m";
        setMessages(prev => [...prev, {
          id: marketId,
          role: "market",
          content: "✅ Market Data Retrieved",
        }]);
        setProgress(40);
        await new Promise(r => setTimeout(r, 800)); // slight delay for effect
      }

      // 2. Clinical Trials
      if (data.results.CLINICAL) {
        setTasks(prev => prev.map(t => t.id === "trials" ? { ...t, status: "complete" } : t));
        const trialsId = Date.now().toString() + "c";
        setMessages(prev => [...prev, {
          id: trialsId,
          role: "trials",
          content: "✅ Clinical Trials Data Retrieved",
        }]);
        setProgress(60);
        await new Promise(r => setTimeout(r, 800));
      }

      // 3. Patents
      if (data.results.PATENTS) {
        setTasks(prev => prev.map(t => t.id === "patent" ? { ...t, status: "complete" } : t));
        const patentId = Date.now().toString() + "p";
        setMessages(prev => [...prev, {
          id: patentId,
          role: "patent",
          content: "✅ Patent Landscape Analyzed",
        }]);
        setProgress(80);
        await new Promise(r => setTimeout(r, 800));
      }

      // 4. Web Intel
      if (data.results.WEB) {
        setTasks(prev => prev.map(t => t.id === "web" ? { ...t, status: "complete" } : t));
        const webId = Date.now().toString() + "w";
        setMessages(prev => [...prev, {
          id: webId,
          role: "web",
          content: "✅ Web Intelligence Gathered",
        }]);
        setProgress(90);
        await new Promise(r => setTimeout(r, 800));
      }

      // 5. Synthesis/Report
      if (data.results.SYNTHESIZED) {
        setTasks(prev => prev.map(t => t.id === "report" ? { ...t, status: "complete" } : t));
        const summaryId = Date.now().toString() + "s";
        setMessages(prev => [...prev, {
          id: summaryId,
          role: "master",
          content: `✅ Analysis Complete. \n\n${data.results.SYNTHESIZED.final_summary || "Report generated."}`,
        }]);
        setProgress(100);

        // Navigate to report with data
        navigate("/report", { state: { molecule: moleculeName, results: data.results } });
      }

    } catch (error) {
      console.error("Error calling backend:", error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: "master",
        content: "❌ Error: Failed to communicate with the research agents.",
      }]);
    } finally {
      setIsProcessing(false);
    }
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
    let moleculeName = "";
    const moleculeMatch = input.match(/(?:molecule|drug)\s+(\w+)/i);
    if (moleculeMatch) {
      moleculeName = moleculeMatch[1];
    } else {
      // If no "molecule X" pattern, try to infer or just use the whole query if short,
      // or the first significant capitalized word.
      const words = input.trim().split(' ');

      // Heuristic: if short enough, treat the whole input as the topic
      if (words.length <= 2) {
        moleculeName = input.trim();
      } else {
        // Find a capitalized word that isn't a common stop word (simple heuristic)
        const potentialDrug = words.find(w => /^[A-Z][a-z]+$/.test(w) && w.length > 3);
        moleculeName = potentialDrug || words[0]; // fallback to first word
      }
    }

    // Clean up
    moleculeName = moleculeName.replace(/[^a-zA-Z0-9- ]/g, "").trim();
    if (!moleculeName) moleculeName = input.slice(0, 15); // Absolute fallback

    // Capitalize first letter
    moleculeName = moleculeName.charAt(0).toUpperCase() + moleculeName.slice(1);

    setInput("");
    await handleApiWorkflow(moleculeName);
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