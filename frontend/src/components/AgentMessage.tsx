import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import TypewriterText from "./TypewriterText";

interface AgentMessageProps {
  role: "user" | "master" | "market" | "trials" | "patent" | "web";
  content: string;
  isTyping?: boolean;
  onTypingComplete?: () => void;
  agentName?: string;
}

const agentConfig = {
  master: {
    name: "Master Agent",
    color: "bg-gradient-to-br from-slate-600 to-slate-700",
    textColor: "text-slate-700",
    icon: Bot
  },
  market: {
    name: "IQVIA Insights Agent",
    color: "bg-gradient-to-br from-primary to-blue-600",
    textColor: "text-primary",
    icon: Bot
  },
  trials: {
    name: "Clinical Trials Agent",
    color: "bg-gradient-to-br from-accent to-teal-600",
    textColor: "text-accent",
    icon: Bot
  },
  patent: {
    name: "Patent Landscape Agent",
    color: "bg-gradient-to-br from-purple-500 to-purple-600",
    textColor: "text-purple-600",
    icon: Bot
  },
  web: {
    name: "Web Intelligence Agent",
    color: "bg-gradient-to-br from-orange-400 to-orange-500",
    textColor: "text-orange-500",
    icon: Bot
  }
};

const AgentMessage = ({ 
  role, 
  content, 
  isTyping = false, 
  onTypingComplete,
  agentName 
}: AgentMessageProps) => {
  const isUser = role === "user";
  const config = isUser ? null : agentConfig[role];
  const Icon = config?.icon || User;

  return (
    <div 
      className={cn(
        "flex gap-3 mb-4 animate-fade-in",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center shrink-0 shadow-md", config?.color)}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      )}
      
      <div className={cn(
        "max-w-[80%] rounded-2xl px-4 py-3 shadow-sm",
        isUser 
          ? "bg-primary text-primary-foreground" 
          : "bg-card border border-border"
      )}>
        {!isUser && config && (
          <p className={cn("text-sm font-semibold mb-1", config.textColor)}>
            {agentName || config.name}
          </p>
        )}
        <div className="text-sm leading-relaxed whitespace-pre-line">
          {isTyping ? (
            <TypewriterText 
              text={content} 
              speed={20}
              onComplete={onTypingComplete}
            />
          ) : (
            content
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center shrink-0 shadow-md">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
};

export default AgentMessage;
