"use client";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, Table, Td, Th } from "@/components/ui/misc";
import { api, type ModelEntry } from "@/lib/api";
import { fmtCredits } from "@/lib/utils";

interface SettingsResp { stored: Record<string, unknown>; effective: Record<string, string | number | boolean | null> }
interface Models { source: string; version: string; video: ModelEntry[]; image: ModelEntry[]; audio: ModelEntry[] }
interface Usage { provider: string; model: string | null; kind: string; count: number; credits: number; cost_usd: number | null }

export default function SettingsPage() {
  const [s, setS] = useState<SettingsResp | null>(null);
  const [m, setM] = useState<Models | null>(null);
  const [u, setU] = useState<Usage[]>([]);
  useEffect(() => {
    api<SettingsResp>("/api/settings").then(setS).catch(() => undefined);
    api<Models>("/api/providers/models").then(setM).catch(() => undefined);
    api<Usage[]>("/api/usage").then(setU).catch(() => undefined);
  }, []);

  return (
    <>
      <PageHeader title="Settings" description="Providers, limits and the live LetzAI model catalogue. API keys are configured server-side via environment variables and are never shown here." />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card><CardHeader><CardTitle>Providers & limits</CardTitle></CardHeader>
          <CardContent>
            <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 text-sm">
              {s && Object.entries(s.effective).map(([k, v]) => (
                <div key={k} className="contents"><dt className="text-muted-foreground">{k.replace(/_/g, " ")}</dt>
                  <dd className="text-right">{typeof v === "boolean" ? <Badge variant={v ? "success" : "secondary"}>{v ? "yes" : "no"}</Badge> : String(v ?? "–")}</dd></div>
              ))}
            </dl>
          </CardContent></Card>
        <Card><CardHeader><CardTitle>Usage (30 days)</CardTitle></CardHeader>
          <CardContent className="p-0">
            <Table><thead><tr><Th>Provider</Th><Th>Kind</Th><Th className="text-right">Count</Th><Th className="text-right">Credits</Th></tr></thead>
              <tbody>{u.map((r, i) => <tr key={i}><Td>{r.provider}<div className="text-xs text-muted-foreground">{r.model}</div></Td><Td>{r.kind}</Td>
                <Td className="text-right tabular-nums">{r.count}</Td><Td className="text-right tabular-nums">{fmtCredits(r.credits)}{r.cost_usd ? <div className="text-xs text-muted-foreground">${r.cost_usd}</div> : null}</Td></tr>)}</tbody></Table>
          </CardContent></Card>
      </div>
      <Card className="mt-6"><CardHeader><CardTitle>LetzAI video models</CardTitle>
        <CardDescription>Catalogue source: {m?.source} {m?.version && `(version ${m.version})`}. Durations and audio support drive scene planning.</CardDescription></CardHeader>
        <CardContent className="p-0">
          <Table><thead><tr><Th>Model</Th><Th>Duration</Th><Th>Resolutions</Th><Th>Audio</Th><Th>References</Th><Th>When to use</Th></tr></thead>
            <tbody>{(m?.video ?? []).map((x) => {
              const v = x.capabilities.video ?? {};
              return <tr key={x.key}><Td><div className="font-medium">{x.displayName}</div><div className="font-mono text-[11px] text-muted-foreground">{x.key}</div></Td>
                <Td className="tabular-nums">{v.duration?.min}–{v.duration?.max}s</Td><Td className="text-xs">{(v.resolutions ?? []).join(", ")}</Td>
                <Td>{v.allowAudio ? <Badge variant="success">native</Badge> : <Badge variant="secondary">none</Badge>}</Td>
                <Td>{v.supportsReference ? "yes" : "–"}</Td><Td className="max-w-sm text-xs text-muted-foreground">{x.useWhen}</Td></tr>;
            })}</tbody></Table>
        </CardContent></Card>
    </>
  );
}
