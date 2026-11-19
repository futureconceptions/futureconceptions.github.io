"use client";
import { AlertTriangle, Check, CircleDashed, Loader2, Pause, X } from "lucide-react";
import { Badge } from "@/components/ui/misc";
import type { PipelineStage, QAReport } from "@/lib/api";
import { cn } from "@/lib/utils";

const STATUS: Record<string, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" | "outline" }> = {
  draft: { label: "Draft", variant: "secondary" },
  queued: { label: "Queued", variant: "default" },
  running: { label: "Running", variant: "default" },
  awaiting_approval: { label: "Needs approval", variant: "warning" },
  awaiting_budget: { label: "Budget check", variant: "warning" },
  completed: { label: "Completed", variant: "success" },
  failed: { label: "Failed", variant: "destructive" },
  cancelled: { label: "Cancelled", variant: "secondary" },
  approved: { label: "QA passed", variant: "success" },
  qa_failed: { label: "Needs review", variant: "warning" },
  superseded: { label: "Superseded", variant: "secondary" },
  pending: { label: "Pending", variant: "secondary" },
  submitting: { label: "Submitting", variant: "default" },
  submitted: { label: "Submitted", variant: "default" },
  succeeded: { label: "Succeeded", variant: "success" },
  generating: { label: "Generating", variant: "default" },
  ready: { label: "Ready", variant: "success" },
};

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS[status] ?? { label: status, variant: "outline" as const };
  const spinning = ["running", "queued", "submitting", "submitted", "generating"].includes(status);
  return <Badge variant={s.variant}>{spinning && <Loader2 className="h-3 w-3 animate-spin" />}{s.label}</Badge>;
}

export function PipelineStepper({ stages, compact = false }: { stages: PipelineStage[]; compact?: boolean }) {
  return (
    <ol className={cn("flex w-full items-center", compact ? "gap-1" : "gap-1.5 overflow-x-auto pb-1")}>
      {stages.map((s, i) => {
        const icon = {
          done: <Check className="h-3.5 w-3.5" />, active: <Loader2 className="h-3.5 w-3.5 animate-spin" />,
          failed: <X className="h-3.5 w-3.5" />, waiting: <Pause className="h-3.5 w-3.5" />,
          cancelled: <X className="h-3.5 w-3.5" />, pending: <CircleDashed className="h-3.5 w-3.5" />,
        }[s.state];
        const color = {
          done: "bg-success text-white", active: "bg-primary text-primary-foreground", failed: "bg-destructive text-white",
          waiting: "bg-warning text-white", cancelled: "bg-muted-foreground/40 text-white", pending: "bg-muted text-muted-foreground",
        }[s.state];
        if (compact) return <li key={s.key} title={`${s.label}: ${s.state}`} className={cn("h-1.5 flex-1 rounded-full", color)} />;
        return (
          <li key={s.key} className="flex min-w-[84px] flex-1 items-center gap-1.5">
            <div className="flex flex-col items-center gap-1">
              <span className={cn("flex h-7 w-7 items-center justify-center rounded-full", color)}>{icon}</span>
              <span className={cn("text-[11px] font-medium", s.state === "pending" ? "text-muted-foreground" : "")}>{s.label}</span>
            </div>
            {i < stages.length - 1 && <div className={cn("mb-4 h-0.5 flex-1 rounded", s.state === "done" ? "bg-success" : "bg-border")} />}
          </li>
        );
      })}
    </ol>
  );
}

const SEV = { low: "secondary", medium: "warning", high: "destructive", critical: "destructive" } as const;

export function QAReportView({ report, title }: { report: QAReport; title?: string }) {
  return (
    <div className="rounded-lg border p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="text-sm font-medium">{title ?? (report.scope === "export" ? "Export QA" : "Scene QA")} · round {report.round}</div>
        <Badge variant={report.passed ? "success" : "destructive"}>{report.passed ? "Passed" : "Failed"}</Badge>
      </div>
      {report.issues.length > 0 && (
        <ul className="mb-2 space-y-1">
          {report.issues.map((i, k) => (
            <li key={k} className="flex items-start gap-2 text-xs">
              <Badge variant={SEV[i.severity]}>{i.severity}</Badge>
              <span><span className="font-medium">{i.check}</span>{i.detail ? ` – ${i.detail}` : ""}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="flex flex-wrap gap-1">
        {report.checks.map((c, k) => (
          <span key={k} title={c.detail}
            className={cn("inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[11px]",
              c.status === "passed" && "border-success/30 text-success",
              c.status === "failed" && "border-destructive/40 text-destructive",
              (c.status === "not_checked" || c.status === "warning") && "border-warning/40 text-warning")}>
            {c.status === "passed" ? <Check className="h-3 w-3" /> : c.status === "failed" ? <X className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
            {c.check}
          </span>
        ))}
      </div>
      <p className="mt-2 text-[11px] text-muted-foreground">Automated checks reduce, but cannot eliminate, visual errors. “not checked” means no tool was configured for that check.</p>
    </div>
  );
}
