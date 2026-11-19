"use client";
import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";
import { CheckCircle2, Download, Pause, RefreshCw, RotateCcw, Square } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { PipelineStepper, QAReportView, StatusBadge } from "@/components/status";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, Badge, Progress, Table, Tabs, Td, Th } from "@/components/ui/misc";
import { api, post, type Concept, type ProjectDetail } from "@/lib/api";
import { fmtCredits, fmtDate, fmtDuration } from "@/lib/utils";

type Tab = "outputs" | "concepts" | "scenes" | "creator" | "research" | "jobs";

export default function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [p, setP] = useState<ProjectDetail | null>(null);
  const [tab, setTab] = useState<Tab>("outputs");
  const [msg, setMsg] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);

  const load = useCallback(() => api<ProjectDetail>(`/api/projects/${id}`).then(setP).catch((e) => setMsg(e.message)), [id]);
  useEffect(() => {
    load();
    const t = setInterval(() => {
      if (!p || ["queued", "running"].includes(p.status)) load();
    }, 3000);
    return () => clearInterval(t);
  }, [load, p]);
  useEffect(() => {
    if (p) setSelected(p.concepts.filter((c) => c.selected).map((c) => c.id));
  }, [p?.id, p?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  async function act(path: string, body?: unknown) {
    setMsg(null);
    try { await post(`/api/projects/${id}${path}`, body); await load(); } catch (e) { setMsg((e as Error).message); }
  }

  if (!p) return <div className="text-sm text-muted-foreground">{msg ?? "Loading…"}</div>;
  const active = ["queued", "running"].includes(p.status);
  const waitingCheckpoint = p.status === "awaiting_approval"
    ? ({ script: "concepts", character: "creator", scenes: "storyboard" } as Record<string, string>)[p.stage] : null;
  const latestExports = Object.values(p.exports.reduce<Record<string, (typeof p.exports)[number]>>((acc, e) => {
    if (!acc[e.concept_id] || acc[e.concept_id].version < e.version) acc[e.concept_id] = e;
    return acc;
  }, {}));
  const jobsDone = p.jobs.filter((j) => ["succeeded", "failed", "cancelled"].includes(j.status)).length;

  return (
    <>
      <PageHeader title={p.name} description={`Created ${fmtDate(p.created_at)} · ${(p.settings.language as string) === "de" ? "Deutsch" : "English"} · ${p.settings.variants} variant(s) · ${p.settings.duration}s`}
        actions={
          <>
            {active && <Button variant="outline" onClick={() => act("/cancel")}><Square />Cancel</Button>}
            {["failed", "cancelled"].includes(p.status) && <Button onClick={() => act("/retry")}><RotateCcw />Resume</Button>}
            {p.status === "awaiting_budget" && <Button onClick={() => act("/confirm-budget", {})}><CheckCircle2 />Confirm budget</Button>}
          </>
        } />

      <Card className="mb-4">
        <CardContent className="space-y-4 p-5">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={p.status} />
            {p.qa_round > 0 && <Badge variant="warning">QA round {p.qa_round}</Badge>}
            <span className="text-sm text-muted-foreground">{p.stage_detail}</span>
          </div>
          <PipelineStepper stages={p.pipeline} />
          {p.jobs.length > 0 && active && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <Progress value={(jobsDone / p.jobs.length) * 100} className="max-w-xs" />{jobsDone}/{p.jobs.length} generation jobs finished
            </div>
          )}
          {p.error && <Alert variant="destructive" title="Pipeline error">{p.error}</Alert>}
          {msg && <Alert variant="destructive">{msg}</Alert>}
          {waitingCheckpoint && (
            <Alert variant="warning" title={`Approval needed: ${waitingCheckpoint}`}>
              <div className="mb-2">{waitingCheckpoint === "concepts" ? "Select the concepts to produce, then approve." : `Review the ${waitingCheckpoint} below, then approve to continue.`}</div>
              <Button size="sm" onClick={() => act("/approve", { checkpoint: waitingCheckpoint,
                ...(waitingCheckpoint === "concepts" ? { selected_concept_ids: selected } : {}) })}><Pause />Approve & continue</Button>
            </Alert>
          )}
          {p.status === "awaiting_budget" && (
            <Alert variant="warning" title="Budget confirmation required">
              Estimated {fmtCredits(p.estimated_credits)} credits vs. budget {fmtCredits(p.budget_credits)}. Confirming raises the budget to the estimate.
            </Alert>
          )}
          <div className="grid gap-3 text-sm sm:grid-cols-4">
            <div><div className="text-xs text-muted-foreground">Estimated</div><div className="font-medium tabular-nums">{fmtCredits(p.estimated_credits)} cr</div></div>
            <div><div className="text-xs text-muted-foreground">Spent</div><div className="font-medium tabular-nums">{fmtCredits(p.spent_credits)} cr</div></div>
            <div><div className="text-xs text-muted-foreground">Budget</div><div className="font-medium tabular-nums">{fmtCredits(p.budget_credits)} cr</div></div>
            <div><div className="text-xs text-muted-foreground">LLM cost</div><div className="font-medium tabular-nums">
              {(() => { const usd = p.usage.filter((u) => u.provider === "anthropic").reduce((a, u) => a + (u.cost_usd ?? 0), 0); return usd ? `$${usd.toFixed(3)}` : "–"; })()}
            </div></div>
          </div>
        </CardContent>
      </Card>

      <div className="mb-4">
        <Tabs value={tab} onChange={setTab} tabs={[
          { value: "outputs", label: "Outputs", count: latestExports.length },
          { value: "concepts", label: "Concepts & scripts", count: p.concepts.length },
          { value: "scenes", label: "Scenes" },
          { value: "creator", label: "Creator" },
          { value: "research", label: "Research" },
          { value: "jobs", label: "Jobs & costs", count: p.jobs.length },
        ]} />
      </div>

      {tab === "outputs" && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {latestExports.length === 0 && <div className="text-sm text-muted-foreground">No exports yet – they appear after the editing stage.</div>}
          {latestExports.map((e) => (
            <Card key={e.id}>
              <CardContent className="space-y-3 p-4">
                <div className="mx-auto aspect-[9/16] w-full max-w-[260px] overflow-hidden rounded-lg bg-black">
                  {e.video_url && <video src={e.video_url} poster={e.thumbnail_url ?? undefined} controls playsInline className="h-full w-full object-contain" />}
                </div>
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0"><div className="truncate font-medium">{e.concept.title}</div>
                    <div className="text-xs text-muted-foreground">v{e.version} · {fmtDuration(e.duration)} · {e.width}×{e.height}</div></div>
                  <StatusBadge status={e.status} />
                </div>
                <div className="flex gap-2">
                  {e.download_url && <Button asChild size="sm" variant="outline"><a href={e.download_url}><Download />MP4</a></Button>}
                  <Button asChild size="sm" variant="ghost"><Link href={`/library/${e.id}`}>Details</Link></Button>
                </div>
                {e.qa && <QAReportView report={e.qa} />}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {tab === "concepts" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {p.concepts.map((c) => <ConceptCard key={c.id} c={c} selectable={waitingCheckpoint === "concepts"}
            checked={selected.includes(c.id)} onToggle={() => setSelected((s) => s.includes(c.id) ? s.filter((x) => x !== c.id) : [...s, c.id])} />)}
        </div>
      )}

      {tab === "scenes" && (
        <div className="space-y-6">
          {p.concepts.filter((c) => c.storyboard).map((c) => (
            <Card key={c.id}>
              <CardHeader><CardTitle className="text-base">{c.title}</CardTitle>
                <CardDescription>{c.storyboard!.video_model} · {c.storyboard!.audio_mode} audio · {fmtDuration(c.storyboard!.total_duration)}</CardDescription></CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {c.storyboard!.scenes.map((s) => {
                  const reports = p.qa_reports.filter((r) => r.scene_id === s.id);
                  return (
                    <div key={s.id} className="space-y-2 rounded-lg border p-3">
                      <div className="aspect-[9/16] overflow-hidden rounded-md bg-muted">
                        {s.video_url ? <video src={s.video_url} poster={s.keyframe_url ?? undefined} controls playsInline className="h-full w-full object-cover" />
                          : s.keyframe_url ? <img src={s.keyframe_url} alt="" className="h-full w-full object-cover" /> : null}
                      </div>
                      <div className="flex flex-wrap items-center gap-1">
                        <Badge variant="secondary">#{s.idx + 1} {s.beat}</Badge><Badge variant="outline">{fmtDuration(s.duration)}</Badge>
                        {s.lipsync_status && <Badge variant={s.lipsync_status === "voiceover" ? "warning" : "secondary"}>{s.lipsync_status}</Badge>}
                        {s.qa_status && <Badge variant={s.qa_status === "passed" ? "success" : s.qa_status === "failed" ? "destructive" : "warning"}>QA {s.qa_status}</Badge>}
                        {s.regen_round > 0 && <Badge variant="warning">regen {s.regen_round}</Badge>}
                      </div>
                      <p className="text-xs">“{s.dialogue}”</p>
                      <details className="text-xs text-muted-foreground"><summary className="cursor-pointer">Direction & prompt</summary>
                        <p className="mt-1"><b>Framing:</b> {s.framing}</p><p><b>Movement:</b> {s.creator_movement}</p>
                        <p><b>Product:</b> {s.product_interaction}</p><p className="mt-1 whitespace-pre-wrap">{s.video_prompt}</p></details>
                      {reports.slice(-1).map((r) => <QAReportView key={r.id} report={r} />)}
                      {!active && <Button size="sm" variant="outline" className="w-full" onClick={() => act(`/scenes/${s.id}/regenerate`)}><RefreshCw />Regenerate scene</Button>}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {tab === "creator" && (p.creator ? (
        <Card><CardContent className="flex flex-col gap-6 p-5 sm:flex-row">
          <div className="aspect-[9/16] w-48 shrink-0 overflow-hidden rounded-lg bg-muted">{p.creator.anchor_url && <img src={p.creator.anchor_url} alt="" className="h-full w-full object-cover" />}</div>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-lg font-semibold">{p.creator.name}<StatusBadge status={p.creator.status} />{p.creator.is_fictional && <Badge variant="secondary">fictional</Badge>}</div>
            <p className="text-muted-foreground">{p.creator.description}</p>
            <dl className="grid grid-cols-[120px_1fr] gap-x-3 gap-y-1 text-xs">
              {Object.entries(p.creator.appearance ?? {}).map(([k, v]) => (
                <div key={k} className="contents"><dt className="text-muted-foreground">{k.replace(/_/g, " ")}</dt><dd>{String(v)}</dd></div>
              ))}
              <dt className="text-muted-foreground">voice</dt><dd>{p.creator.voice?.preset} ({p.creator.voice?.language})</dd>
            </dl>
            <Button asChild size="sm" variant="outline"><Link href="/creators">Open creator library</Link></Button>
          </div>
        </CardContent></Card>
      ) : <div className="text-sm text-muted-foreground">The creator is cast in the Character stage.</div>)}

      {tab === "research" && p.product && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card><CardHeader><CardTitle className="text-base">Input</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {p.product.url && <div><span className="text-muted-foreground">URL: </span><a className="text-primary underline" href={p.product.url} target="_blank" rel="noreferrer">{p.product.url}</a> <Badge variant="secondary">{p.product.fetch_status}</Badge></div>}
              {p.product.description && <p className="whitespace-pre-wrap">{p.product.description}</p>}
              <div className="flex flex-wrap gap-2">{p.product.assets.map((a) => <img key={a.id} src={a.url} alt="" className="h-20 w-20 rounded border object-cover" />)}</div>
            </CardContent></Card>
          <ResearchPanel research={p.product.research as Research | null} />
        </div>
      )}

      {tab === "jobs" && (
        <Card><CardContent className="p-0">
          <Table>
            <thead><tr><Th>Purpose</Th><Th>Provider / model</Th><Th>Status</Th><Th>Attempts</Th><Th>Provider job ID</Th><Th className="text-right">Credits</Th><Th>Started</Th><Th /></tr></thead>
            <tbody>
              {p.jobs.map((j) => (
                <tr key={j.id}>
                  <Td>{j.purpose}{j.round > 0 && <span className="text-xs text-muted-foreground"> · r{j.round}</span>}{j.candidate_index > 0 && <span className="text-xs text-muted-foreground"> · c{j.candidate_index}</span>}</Td>
                  <Td className="text-xs">{j.provider}<div className="text-muted-foreground">{j.model}</div></Td>
                  <Td><StatusBadge status={j.status} />{j.error && <div className="mt-1 max-w-xs truncate text-xs text-destructive" title={j.error}>{j.error}</div>}</Td>
                  <Td className="tabular-nums">{j.attempts}/{j.max_attempts}</Td>
                  <Td className="font-mono text-[11px]">{j.provider_job_id ?? "–"}</Td>
                  <Td className="text-right tabular-nums">{fmtCredits(j.actual_credits ?? j.estimated_credits)}{j.actual_credits == null && <span className="text-muted-foreground"> est</span>}</Td>
                  <Td className="text-xs">{fmtDate(j.submitted_at)}</Td>
                  <Td>{j.status === "failed" && <Button size="sm" variant="ghost" onClick={async () => { await post(`/api/jobs/${j.id}/retry`); load(); }}><RotateCcw />Retry</Button>}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
          <div className="border-t p-4 text-sm">
            <div className="mb-2 font-medium">Usage by provider</div>
            {p.usage.map((u) => <div key={u.provider + u.kind} className="flex justify-between text-xs"><span>{u.provider} · {u.kind} ×{u.count}</span>
              <span className="tabular-nums">{fmtCredits(u.credits)} cr{u.cost_usd ? ` · $${u.cost_usd}` : ""}</span></div>)}
          </div>
        </CardContent></Card>
      )}
    </>
  );
}

function ConceptCard({ c, selectable, checked, onToggle }: { c: Concept; selectable: boolean; checked: boolean; onToggle: () => void }) {
  const problems = c.script?.beats?.[0]?.validation ?? [];
  return (
    <Card className={c.selected ? "border-primary/40" : "opacity-80"}>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div><CardTitle className="text-base">{c.title}</CardTitle><CardDescription>{c.angle.replace(/_/g, " ")} · {c.target_duration}s · score {c.score.toFixed(1)}</CardDescription></div>
          {selectable ? <input type="checkbox" checked={checked} onChange={onToggle} className="mt-1 h-4 w-4" /> : c.selected && <Badge>selected</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div><span className="text-xs font-medium uppercase text-muted-foreground">Hook</span><p>{c.hook}</p></div>
        <div><span className="text-xs font-medium uppercase text-muted-foreground">Core message</span><p>{c.core_message}</p></div>
        <div className="grid grid-cols-2 gap-3 text-xs"><div><b>Emotion:</b> {c.emotional_angle}</div><div><b>CTA:</b> {c.cta}</div></div>
        <div className="text-xs"><b>Visual:</b> {c.visual_concept}</div>
        {c.script && (
          <div className="rounded-md bg-muted p-3">
            <div className="mb-1 text-xs font-medium">Script ({c.script.word_count} words)</div>
            {c.script.beats.map((b, i) => <p key={i} className="text-xs"><Badge variant="outline" className="mr-1">{b.beat} {b.seconds.toFixed(1)}s</Badge>{b.dialogue}</p>)}
          </div>
        )}
        {c.claims_used.length > 0 && <div className="text-xs text-muted-foreground"><b>Claims used:</b> {c.claims_used.join(" · ")}</div>}
        {problems.length > 0 && <Alert variant="warning">{problems.join("; ")}</Alert>}
      </CardContent>
    </Card>
  );
}

interface Research {
  product_name: string; summary: string; claims_to_avoid: string[];
  supported_claims: { claim: string; evidence: string; source_ref?: string | null; source_url?: string | null; source: string }[];
  sources?: { id: string; title: string; url: string | null; source: string; chars: number }[];
  search?: { method: string; metric: string; effort: string; agents: number; messages: number;
    turns: Record<string, number>; fused_ranking: [string, number][]; rejected_claims: number };
}

function ResearchPanel({ research }: { research: Research | null }) {
  if (!research) return <div className="text-sm text-muted-foreground">Research runs in the first stage.</div>;
  const src = Object.fromEntries((research.sources ?? []).map((s) => [s.id, s]));
  const unverified = research.claims_to_avoid.filter((c) => c.startsWith("UNVERIFIED"));
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Evidence-backed claims</CardTitle>
        <CardDescription>Every claim quotes a passage found by the search agents and is checked against the source text. Only these may be used in scripts.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {research.search && (
          <div className="flex flex-wrap gap-1.5 text-xs">
            <Badge variant="secondary">{research.search.agents} search agent(s)</Badge>
            <Badge variant="secondary">objective {research.search.metric}</Badge>
            <Badge variant="secondary">effort {research.search.effort}</Badge>
            <Badge variant="secondary">{research.search.messages} message(s)</Badge>
            {research.search.rejected_claims > 0 && <Badge variant="warning">{research.search.rejected_claims} unverified claim(s) removed</Badge>}
          </div>
        )}
        <ol className="space-y-2">
          {research.supported_claims.map((c, i) => {
            const doc = c.source_ref ? src[c.source_ref.split("#")[0]] : undefined;
            return (
              <li key={i} className="rounded-md border p-2">
                <div className="font-medium">{c.claim}</div>
                <blockquote className="mt-1 border-l-2 pl-2 text-xs text-muted-foreground">“{c.evidence}”</blockquote>
                <div className="mt-1 text-[11px] text-muted-foreground">
                  <span className="font-mono">{c.source_ref}</span>
                  {doc && <> · {doc.url ? <a className="text-primary underline" href={doc.url} target="_blank" rel="noreferrer">{doc.title || doc.url}</a> : doc.title}</>}
                </div>
              </li>
            );
          })}
          {research.supported_claims.length === 0 && <li className="text-muted-foreground">No verifiable claims were found.</li>}
        </ol>
        {unverified.length > 0 && <Alert variant="warning" title="Removed (no source text)">{unverified.map((u) => u.replace("UNVERIFIED (no source text): ", "")).join(" · ")}</Alert>}
        {research.sources && (
          <div>
            <div className="mb-1 text-xs font-medium uppercase text-muted-foreground">Searched corpus</div>
            <ul className="space-y-0.5 text-xs">
              {research.sources.map((s) => (
                <li key={s.id}><span className="font-mono">{s.id}</span> · {s.source.replace("_", " ")} · {s.url ? <a className="text-primary underline" href={s.url} target="_blank" rel="noreferrer">{s.title || s.url}</a> : s.title} <span className="text-muted-foreground">({s.chars} chars)</span></li>
              ))}
            </ul>
          </div>
        )}
        <details className="text-xs"><summary className="cursor-pointer text-muted-foreground">Raw research & search trace</summary>
          <pre className="mt-2 max-h-[420px] overflow-auto rounded bg-muted p-3">{JSON.stringify(research, null, 2)}</pre></details>
      </CardContent>
    </Card>
  );
}
