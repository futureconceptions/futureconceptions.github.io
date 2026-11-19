"use client";
import Link from "next/link";
import { use, useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { QAReportView, StatusBadge } from "@/components/status";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/misc";
import { api, type Concept, type ExportItem, type QAReport } from "@/lib/api";
import { fmtDate, fmtDuration } from "@/lib/utils";

interface ExportDetail extends ExportItem {
  concept_detail: Concept | null;
  product?: { name: string | null; brand_name: string | null; url: string | null; description: string | null; research: Record<string, unknown> | null };
  settings: Record<string, unknown>;
  versions: ExportItem[];
  scene_qa: QAReport[];
}

export default function ExportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [e, setE] = useState<ExportDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { api<ExportDetail>(`/api/exports/${id}`).then(setE).catch((x) => setErr(x.message)); }, [id]);
  if (!e) return <div className="text-sm text-muted-foreground">{err ?? "Loading…"}</div>;
  const c = e.concept_detail;

  return (
    <>
      <PageHeader title={e.concept.title} description={`Version ${e.version} · ${fmtDate(e.created_at)}`}
        actions={<>
          {e.download_url && <Button asChild><a href={e.download_url}><Download />Download MP4</a></Button>}
          {e.subtitles_url && <Button asChild variant="outline"><a href={e.subtitles_url}><FileText />Captions (.srt)</a></Button>}
          <Button asChild variant="ghost"><Link href={`/projects/${e.project_id}`}>Open project</Link></Button>
        </>} />
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4">
          <div className="aspect-[9/16] overflow-hidden rounded-xl bg-black">
            {e.video_url && <video src={e.video_url} poster={e.thumbnail_url ?? undefined} controls playsInline className="h-full w-full object-contain" />}
          </div>
          <div className="flex flex-wrap gap-1.5"><StatusBadge status={e.status} /><Badge variant="outline">{e.width}×{e.height}</Badge>
            <Badge variant="outline">{fmtDuration(e.duration)}</Badge><Badge variant="outline">H.264 / AAC</Badge></div>
          <Card><CardHeader><CardTitle className="text-base">Versions</CardTitle></CardHeader>
            <CardContent className="space-y-1 text-sm">
              {e.versions.map((v) => (
                <Link key={v.id} href={`/library/${v.id}`} className={`flex items-center justify-between rounded px-2 py-1 hover:bg-muted ${v.id === e.id ? "bg-muted" : ""}`}>
                  <span>v{v.version} · {fmtDate(v.created_at)}</span><StatusBadge status={v.status} />
                </Link>
              ))}
            </CardContent></Card>
        </div>
        <div className="space-y-4">
          {e.qa && <QAReportView report={e.qa} title="Final export QA" />}
          {c?.script && (
            <Card><CardHeader><CardTitle className="text-base">Script</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="text-xs text-muted-foreground">{c.angle.replace(/_/g, " ")} · {c.script.language} · {c.script.word_count} words · CTA: {c.cta}</div>
                {c.script.beats.map((b, i) => <p key={i}><Badge variant="outline" className="mr-2">{b.beat}</Badge>{b.dialogue}</p>)}
                {c.claims_used.length > 0 && <p className="text-xs text-muted-foreground"><b>Supported claims used:</b> {c.claims_used.join(" · ")}</p>}
              </CardContent></Card>
          )}
          {c?.storyboard && (
            <Card><CardHeader><CardTitle className="text-base">Scenes & scene QA</CardTitle></CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2">
                {c.storyboard.scenes.map((s) => (
                  <div key={s.id} className="space-y-2 rounded-lg border p-3 text-xs">
                    <div className="flex flex-wrap gap-1"><Badge variant="secondary">#{s.idx + 1} {s.beat}</Badge><Badge variant="outline">{fmtDuration(s.duration)}</Badge>
                      {s.lipsync_status && <Badge variant="outline">{s.lipsync_status}</Badge>}</div>
                    <p>“{s.dialogue}”</p>
                    {e.scene_qa.filter((r) => r.scene_id === s.id).slice(-1).map((r) => <QAReportView key={r.id} report={r} />)}
                  </div>
                ))}
              </CardContent></Card>
          )}
          <Card><CardHeader><CardTitle className="text-base">Product & generation settings</CardTitle></CardHeader>
            <CardContent className="grid gap-4 text-xs md:grid-cols-2">
              <div className="space-y-1">
                <div><b>Product:</b> {e.product?.name} {e.product?.brand_name && `(${e.product.brand_name})`}</div>
                {e.product?.url && <div className="truncate"><b>URL:</b> {e.product.url}</div>}
                {e.product?.description && <p className="text-muted-foreground">{e.product.description}</p>}
              </div>
              <pre className="overflow-auto rounded bg-muted p-2">{JSON.stringify({ ...e.settings, edit: e.edit_settings }, null, 2)}</pre>
            </CardContent></Card>
        </div>
      </div>
    </>
  );
}
