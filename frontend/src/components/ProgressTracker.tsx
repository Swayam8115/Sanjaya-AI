import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Task {
  id: string;
  label: string;
  emoji: string;
  status: "pending" | "loading" | "complete";
}

interface ProgressTrackerProps {
  tasks: Task[];
  progress: number;
}

const ProgressTracker = ({ tasks, progress }: ProgressTrackerProps) => {
  return (
    <div className="bg-card rounded-xl p-6 shadow-lg border border-border animate-fade-in">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-foreground">Research Progress</span>
          <span className="text-sm font-semibold text-primary">{progress}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
      <div className="space-y-3">
        {tasks.map((task) => (
          <div 
            key={task.id} 
            className={cn(
              "flex items-center gap-3 transition-all duration-300",
              task.status === "complete" && "opacity-100",
              task.status === "loading" && "opacity-100",
              task.status === "pending" && "opacity-50"
            )}
          >
            {task.status === "complete" && (
              <CheckCircle2 className="w-5 h-5 text-success shrink-0 animate-scale-in" />
            )}
            {task.status === "loading" && (
              <Loader2 className="w-5 h-5 text-primary shrink-0 animate-spin" />
            )}
            {task.status === "pending" && (
              <Circle className="w-5 h-5 text-muted-foreground shrink-0" />
            )}
            <span className="text-sm">
              {task.emoji} {task.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressTracker;
