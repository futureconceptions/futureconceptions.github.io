"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Download, Film } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { StatusBadge } from "@/components/status";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState, Tabs } from "@/components/ui/misc";
import { api, type ExportItem } from "@/lib/api";
import { fmtDate, fmtDuration } from "@/lib/utils";

type F = "current" | "approved" | "qa_failed" | "all";

export default function LibraryPage() {
  const [items, setItems] = useState<ExportItem[] | null>(null);
  const [f, setF] = useState<F>("current");
  useEffect(() => { api<ExportItem[]>("/api/exports").then(setItems).catch(() => undefined); }, []);
  const list = (items ?? []).filter((e) => f === "all" ? true : f === "current" ? e.status !== "superseded" : e.status === f);

  return (
    <>
      <PageHeader title="Advertisement library" description="Finished ads with scripts, settings, version history and QA reports." />
      <div className="mb-4"><Tabs value={f} onChange={setF} tabs={[
        { value: "current", label: "Current" }, { value: "approved", label: "QA passed" },
        { value: "qa_failed", label: "Needs review" }, { value: "all", label: "All versions" }]} /></div>
      {items && list.length === 0 && <EmptyState icon={<Film className="h-6 w-6" />} title="No advertisements yet" />}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {list.map((e) => (
          <Card key={e.id} className="overflow-hidden">
            <div className="aspect-[9/16] bg-black">
              {e.video_url && <video src={e.video_url} poster={e.thumbnail_url ?? undefined} controls preload="none" playsInline className="h-full w-full object-contain" />}
            </div>
            <CardContent className="space-y-2 p-4">
              <div className="flex items-center justify-between gap-2"><span className="truncate text-sm font-medium">{e.concept.title}</span><StatusBadge status={e.status} /></div>
              <div className="text-xs text-muted-foreground">{e.project?.name} · v{e.version} · {fmtDuration(e.duration)} · {fmtDate(e.created_at)}</div>
              <p className="line-clamp-2 text-xs">“{e.concept.hook}”</p>
              <div className="flex gap-2">
                {e.download_url && <Button asChild size="sm" variant="outline"><a href={e.download_url}><Download />MP4</a></Button>}
                <Button asChild size="sm" variant="ghost"><Link href={`/library/${e.id}`}>Details</Link></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
