"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Coins, Film, Loader2, Plus, XCircle } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { PipelineStepper, StatusBadge } from "@/components/status";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, Progress } from "@/components/ui/misc";
import { api, type Dashboard } from "@/lib/api";
import { fmtCredits, fmtDate } from "@/lib/utils";

function Stat({ label, value, icon, hint }: { label: string; value: React.ReactNode; icon: React.ReactNode; hint?: string }) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between p-5">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
          <div className="mt-1.5 text-2xl font-semibold tabular-nums">{value}</div>
          {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
        </div>
        <div className="rounded-lg bg-accent p-2 text-accent-foreground">{icon}</div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [d, setD] = useState<Dashboard | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () => api<Dashboard>("/api/dashboard").then((x) => alive && setD(x)).catch((e) => setErr(e.message));
    load();
    const t = setInterval(load, 5000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  if (err) return <div className="text-sm text-destructive">{err}</div>;
  if (!d) return <div className="text-sm text-muted-foreground">Loading dashboard…</div>;
  const budgetPct = (d.global_committed_this_month / Math.max(1, d.global_budget_credits)) * 100;

  return (
    <>
      <PageHeader title="Dashboard" description="Production overview across all your advertisement projects."
        actions={<Button asChild><Link href="/new"><Plus />New advertisement</Link></Button>} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Stat label="Generated ads" value={d.total_ads} icon={<Film className="h-4 w-4" />} hint={`${d.needs_review} need review`} />
        <Stat label="Active jobs" value={d.active_jobs} icon={<Loader2 className="h-4 w-4" />} hint={`${d.active_projects} running projects`} />
        <Stat label="Completed videos" value={d.completed_videos} icon={<CheckCircle2 className="h-4 w-4" />} hint="passed QA" />
        <Stat label="Failed jobs" value={d.failed_jobs} icon={<XCircle className="h-4 w-4" />} hint={`${d.failed_projects} failed projects`} />
        <Stat label="Credits spent" value={fmtCredits(d.credits_spent)} icon={<Coins className="h-4 w-4" />}
          hint={d.estimated_cost_usd != null ? `≈ $${d.estimated_cost_usd}` : "LetzAI credits"} />
      </div>
      <Card className="mt-4">
        <CardContent className="p-5">
          <div className="mb-2 flex justify-between text-sm">
            <span className="font-medium">Global monthly budget</span>
            <span className="tabular-nums text-muted-foreground">
              {fmtCredits(d.global_committed_this_month)} / {fmtCredits(d.global_budget_credits)} credits
            </span>
          </div>
          <Progress value={budgetPct} />
          {budgetPct > 85 && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-warning">
              <AlertTriangle className="h-3.5 w-3.5" />Approaching the global spending limit.
            </div>
          )}
        </CardContent>
      </Card>
      <Card className="mt-6">
        <CardHeader><CardTitle>Recent projects</CardTitle></CardHeader>
        <CardContent>
          {d.recent_projects.length === 0 ? (
            <EmptyState icon={<Film className="h-6 w-6" />} title="No projects yet">
              Submit a product URL, description or images and the factory produces finished ads.
            </EmptyState>
          ) : (
            <div className="divide-y">
              {d.recent_projects.map((p) => (
                <Link key={p.id} href={`/projects/${p.id}`} className="flex items-center gap-4 py-3 hover:bg-muted/40">
                  <div className="h-14 w-8 shrink-0 overflow-hidden rounded bg-muted">
                    {p.thumbnail_url && <img src={p.thumbnail_url} alt="" className="h-full w-full object-cover" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">{p.name}</span>
                      <StatusBadge status={p.status} />
                    </div>
                    <div className="mt-1.5 max-w-md"><PipelineStepper stages={p.pipeline} compact /></div>
                    <div className="mt-1 truncate text-xs text-muted-foreground">{p.error ?? p.stage_detail ?? fmtDate(p.created_at)}</div>
                  </div>
                  <div className="hidden text-right text-xs tabular-nums text-muted-foreground sm:block">
                    {fmtCredits(p.spent_credits)} / {fmtCredits(p.budget_credits)} cr
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
