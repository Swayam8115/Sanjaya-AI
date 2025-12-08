import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";
import AgentMessage from "@/components/AgentMessage";
import ProgressTracker from "@/components/ProgressTracker";
import sanjayaLogo from "@/assets/sanjaya-logo.png";
import { sendMessageStream } from "@/api";

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

  const masterId = Date.now().toString();
  setMessages(prev => [...prev, {
    id: masterId,
    role: "master",
    content: "Understood. Orchestrating agents to research your query...",
  }]);

  const agentToTaskMap: Record<string, Task> = {
    "IQVIA Insights Agent": { id: "market", label: "Market Data", emoji: "📊", status: "pending" },
    "Clinical Trials Agent": { id: "trials", label: "Clinical Trials", emoji: "🧬", status: "pending" },
    "Patent Landscape Agent": { id: "patent", label: "Patent Landscape", emoji: "📜", status: "pending" },
    "Web Intelligence Agent": { id: "web", label: "Web Intelligence", emoji: "🌐", status: "pending" },
    "EXIM Trends Agent": { id: "exim", label: "EXIM Trends", emoji: "🚢", status: "pending" },
    "Internal Knowledge Agent": { id: "internal", label: "Internal Knowledge", emoji: "📚", status: "pending" },
  };

  const agentRoleMap: Record<string, Message["role"]> = {
    "IQVIA Insights Agent": "market",
    "Clinical Trials Agent": "trials",
    "Patent Landscape Agent": "patent",
    "Web Intelligence Agent": "web",
    "EXIM Trends Agent": "web",
    "Internal Knowledge Agent": "web",
  };

  try {
    await sendMessageStream(input, (event) => {
      switch (event.type) {
        case "agents_selected":
          // Create tasks immediately when agents are selected
          const initialTasks: Task[] = event.selected_agents.map(
            (agentName: string) => agentToTaskMap[agentName]
          ).filter(Boolean);
          
          initialTasks.push({ 
            id: "report", 
            label: "Report Generation", 
            emoji: "🧾", 
            status: "pending" 
          });
          
          setTasks(initialTasks);
          setProgress(10);
          break;

        case "agent_started":
          setTasks(prev => prev.map(t => 
            t.id === agentToTaskMap[event.agent_name]?.id 
              ? { ...t, status: "loading" } 
              : t
          ));
          break;

        case "agent_completed":
          setTasks(prev => prev.map(t => 
            t.id === agentToTaskMap[event.agent_name]?.id 
              ? { ...t, status: "complete" } 
              : t
          ));
          
          // Clean up the agent name for display
          const cleanAgentName = event.agent_name.replace(" Agent", "");
          
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: (agentRoleMap[event.agent_name] || "master") as Message["role"],
            content: `✅ ${cleanAgentName} Data Retrieved`,
          }]);
          
          setProgress(prev => Math.min(prev + 15, 80));
          break;

        case "synthesis_completed":
          setProgress(90);
          break;

        case "report_completed":
          setTasks(prev => prev.map(t => 
            t.id === "report" ? { ...t, status: "complete" } : t
          ));
          setProgress(100);
          break;

        case "completed":
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: "master",
            content: `✅ Analysis Complete.`,
          }]);
          
          navigate("/report", { 
            state: { molecule: moleculeName, results: event.results } 
          });
          break;

        case "error":
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: "master",
            content: `❌ Error: ${event.message}`,
          }]);
          break;
      }
    });
  } catch (error) {
    console.error("Error:", error);
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