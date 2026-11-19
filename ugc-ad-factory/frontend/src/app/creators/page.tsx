"use client";
import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, RefreshCw, Trash2, Upload, UserPlus, Users } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { StatusBadge } from "@/components/status";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select, Switch, Textarea } from "@/components/ui/input";
import { Alert, Badge, EmptyState } from "@/components/ui/misc";
import { api, post, type Creator } from "@/lib/api";

const VOICES = ["friendly-young", "bright-host", "warm-narrator", "calm-guide", "crisp-news", "deep-trailer"];

export default function CreatorsPage() {
  const [items, setItems] = useState<Creator[] | null>(null);
  const [open, setOpen] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", description: "", hair: "", face: "", clothing: "", environment: "", age: "25-34",
    voice_preset: "friendly-young", language: "en", is_fictional: true, consent_person_name: "", consent_reference: "", consent_confirmed: false });

  const load = useCallback(() => api<Creator[]>("/api/creators").then(setItems).catch((e) => setErr(e.message)), []);
  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  async function create() {
    setErr(null);
    try {
      await post("/api/creators", {
        name: form.name, description: form.description || undefined, voice_preset: form.voice_preset, language: form.language,
        appearance: Object.fromEntries(Object.entries({ age_range: form.age, hair: form.hair, face: form.face, clothing: form.clothing,
          environment: form.environment }).filter(([, v]) => v)),
        is_fictional: form.is_fictional,
        ...(form.is_fictional ? {} : { consent_person_name: form.consent_person_name, consent_reference: form.consent_reference,
          consent_confirmed: form.consent_confirmed, generate_anchor: false }),
      });
      setOpen(false);
      load();
    } catch (e) { setErr((e as Error).message); }
  }

  async function upload(c: Creator, file: File) {
    const fd = new FormData();
    fd.append("image", file);
    try { await post(`/api/creators/${c.id}/references?set_as_anchor=true`, fd); load(); } catch (e) { setErr((e as Error).message); }
  }

  return (
    <>
      <PageHeader title="Creator library" description="Reusable AI creators. Each keeps an anchor image and voice so it looks and sounds the same across ads."
        actions={<Button onClick={() => setOpen((o) => !o)}><UserPlus />New creator</Button>} />
      {err && <div className="mb-4"><Alert variant="destructive">{err}</Alert></div>}
      {open && (
        <Card className="mb-6">
          <CardHeader><CardTitle>New creator</CardTitle><CardDescription>Fictional creators get a generated anchor portrait. Real people require documented consent and an uploaded reference image.</CardDescription></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5"><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Age range</Label><Input value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Hair</Label><Input value={form.hair} onChange={(e) => setForm({ ...form, hair: e.target.value })} placeholder="short curly black hair" /></div>
            <div className="space-y-1.5"><Label>Face & features</Label><Input value={form.face} onChange={(e) => setForm({ ...form, face: e.target.value })} placeholder="warm brown eyes, light stubble" /></div>
            <div className="space-y-1.5"><Label>Clothing</Label><Input value={form.clothing} onChange={(e) => setForm({ ...form, clothing: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Environment</Label><Input value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value })} /></div>
            <div className="space-y-1.5"><Label>Voice</Label>
              <Select value={form.voice_preset} onChange={(e) => setForm({ ...form, voice_preset: e.target.value })}>{VOICES.map((v) => <option key={v}>{v}</option>)}</Select></div>
            <div className="space-y-1.5"><Label>Voice language</Label>
              <Select value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}><option value="en">English</option><option value="de">Deutsch</option></Select></div>
            <div className="space-y-1.5 sm:col-span-2"><Label>Notes</Label><Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            <div className="sm:col-span-2"><Switch checked={!form.is_fictional} onChange={(v) => setForm({ ...form, is_fictional: !v })} label="This creator depicts a real person" /></div>
            {!form.is_fictional && (
              <div className="grid gap-4 rounded-lg border border-warning/40 bg-warning/5 p-4 sm:col-span-2 sm:grid-cols-2">
                <div className="space-y-1.5"><Label>Person who consented</Label><Input value={form.consent_person_name} onChange={(e) => setForm({ ...form, consent_person_name: e.target.value })} /></div>
                <div className="space-y-1.5"><Label>Consent reference (contract / release ID)</Label><Input value={form.consent_reference} onChange={(e) => setForm({ ...form, consent_reference: e.target.value })} /></div>
                <label className="flex items-start gap-2 text-xs sm:col-span-2"><input type="checkbox" checked={form.consent_confirmed} onChange={(e) => setForm({ ...form, consent_confirmed: e.target.checked })} className="mt-0.5" />
                  I confirm this person granted written permission to use their likeness (and voice, if cloned) for AI-generated advertising.</label>
              </div>
            )}
            <div className="flex gap-2 sm:col-span-2"><Button disabled={!form.name} onClick={create}>Create</Button><Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button></div>
          </CardContent>
        </Card>
      )}
      {items && items.length === 0 && <EmptyState icon={<Users className="h-6 w-6" />} title="No creators yet">Creators are also generated automatically for each project and saved here.</EmptyState>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {(items ?? []).map((c) => (
          <Card key={c.id} className="overflow-hidden">
            <div className="aspect-[3/4] bg-muted">{c.anchor_url && <img src={c.anchor_url} alt={c.name} className="h-full w-full object-cover" />}</div>
            <CardContent className="space-y-2 p-4">
              <div className="flex items-center justify-between gap-2"><span className="truncate font-medium">{c.name}</span><StatusBadge status={c.status} /></div>
              <div className="flex flex-wrap gap-1">
                <Badge variant="secondary">{c.voice?.preset ?? "voice"}</Badge>
                <Badge variant={c.is_fictional ? "secondary" : "warning"}>{c.is_fictional ? "fictional" : "real · consent on file"}</Badge>
                <Badge variant="outline">{c.references.length} refs</Badge>
              </div>
              <p className="line-clamp-2 text-xs text-muted-foreground">{c.description ?? c.anchor_prompt}</p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {c.anchor_url && c.status !== "approved" && <Button size="sm" variant="outline" onClick={async () => { await post(`/api/creators/${c.id}/approve`); load(); }}><CheckCircle2 />Approve</Button>}
                {c.is_fictional && <Button size="sm" variant="outline" onClick={async () => { try { await post(`/api/creators/${c.id}/regenerate-anchor`); load(); } catch (e) { setErr((e as Error).message); } }}><RefreshCw />Replace look</Button>}
                <label className="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-md border px-3 text-xs hover:bg-accent">
                  <Upload className="h-3.5 w-3.5" />Reference<input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => e.target.files?.[0] && upload(c, e.target.files[0])} />
                </label>
                <Button size="sm" variant="ghost" aria-label="Delete" onClick={async () => { if (confirm(`Delete ${c.name}?`)) { await api(`/api/creators/${c.id}`, { method: "DELETE" }); load(); } }}><Trash2 /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
