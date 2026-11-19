"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, Workflow } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { PipelineStepper, StatusBadge } from "@/components/status";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState, Tabs } from "@/components/ui/misc";
import { api, type ProjectSummary } from "@/lib/api";
import { fmtCredits, fmtDate } from "@/lib/utils";

type Filter = "all" | "active" | "attention" | "completed";

export default function ProjectsPage() {
  const [items, setItems] = useState<ProjectSummary[] | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    const load = () => api<ProjectSummary[]>("/api/projects").then(setItems).catch(() => undefined);
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  const groups: Record<Filter, (p: ProjectSummary) => boolean> = {
    all: () => true,
    active: (p) => ["queued", "running"].includes(p.status),
    attention: (p) => ["awaiting_approval", "awaiting_budget", "failed"].includes(p.status),
    completed: (p) => p.status === "completed",
  };
  const list = (items ?? []).filter(groups[filter]);

  return (
    <>
      <PageHeader title="Production monitor" description="Research → Script → Character → Scenes → Video → Voice → Lip Sync → Editing → QA → Export"
        actions={<Button asChild><Link href="/new"><Plus />New advertisement</Link></Button>} />
      <div className="mb-4">
        <Tabs value={filter} onChange={setFilter} tabs={(["all", "active", "attention", "completed"] as Filter[]).map((v) => ({
          value: v, label: { all: "All", active: "Active", attention: "Needs attention", completed: "Completed" }[v],
          count: (items ?? []).filter(groups[v]).length }))} />
      </div>
      {items && list.length === 0 && <EmptyState icon={<Workflow className="h-6 w-6" />} title="Nothing here" />}
      <div className="grid gap-3">
        {list.map((p) => (
          <Link key={p.id} href={`/projects/${p.id}`}>
            <Card className="transition-shadow hover:shadow-md">
              <CardContent className="p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className="font-medium">{p.name}</span>
                  <StatusBadge status={p.status} />
                  <span className="ml-auto text-xs text-muted-foreground">{fmtDate(p.created_at)} · {fmtCredits(p.spent_credits)} / {fmtCredits(p.budget_credits)} credits</span>
                </div>
                <PipelineStepper stages={p.pipeline} />
                {(p.error || p.stage_detail) && (
                  <div className={p.error ? "mt-2 text-xs text-destructive" : "mt-2 text-xs text-muted-foreground"}>{p.error ?? p.stage_detail}</div>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </>
  );
}
