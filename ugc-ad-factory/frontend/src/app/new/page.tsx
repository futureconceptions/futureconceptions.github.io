"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Coins, ImagePlus, Sparkles, X } from "lucide-react";
import { PageHeader } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Select, Switch, Textarea } from "@/components/ui/input";
import { Alert, Separator, Tabs } from "@/components/ui/misc";
import { api, post, type Creator, type Estimate, type ModelEntry, type ProjectSummary } from "@/lib/api";
import { fmtCredits } from "@/lib/utils";

type Mode = "simple" | "advanced";

const DEFAULTS = {
  name: "", product_name: "", product_url: "", product_description: "", brand_name: "", brand_guidelines: "", target_audience: "",
  language: "en" as "en" | "de", duration: 20, variants: 2, cta: "",
  creator_id: "", gender: "", age_range: "", appearance: "", clothing: "", environment: "",
  video_model: "", audio_mode: "auto", resolution: "720p", video_candidates: 1, keyframes: "per_scene",
  subtitles: true, end_card: true, music: false, budget_credits: "",
  cp_concepts: false, cp_creator: false, cp_storyboard: false,
};

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export default function NewAdPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("simple");
  const [f, setF] = useState(DEFAULTS);
  const [images, setImages] = useState<File[]>([]);
  const [licensed, setLicensed] = useState(false);
  const [creators, setCreators] = useState<Creator[]>([]);
  const [videoModels, setVideoModels] = useState<ModelEntry[]>([]);
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [estErr, setEstErr] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = <K extends keyof typeof DEFAULTS>(k: K, v: (typeof DEFAULTS)[K]) => setF((s) => ({ ...s, [k]: v }));

  useEffect(() => {
    api<Creator[]>("/api/creators").then((c) => setCreators(c.filter((x) => x.anchor_url))).catch(() => undefined);
    api<{ video: ModelEntry[] }>("/api/providers/models").then((m) => setVideoModels(m.video)).catch(() => undefined);
  }, []);

  const payload = useMemo(() => {
    const prefs = Object.fromEntries(Object.entries({ gender: f.gender, age_range: f.age_range, appearance: f.appearance,
      clothing: f.clothing, environment: f.environment }).filter(([, v]) => v));
    const checkpoints = [f.cp_concepts && "concepts", f.cp_creator && "creator", f.cp_storyboard && "storyboard"].filter(Boolean);
    const p: Record<string, unknown> = {
      name: f.name || undefined, product_name: f.product_name || undefined, product_url: f.product_url || undefined, product_description: f.product_description || undefined,
      brand_name: f.brand_name || undefined, language: f.language, duration: Number(f.duration), variants: Number(f.variants),
      cta: f.cta || undefined, assets_licensed: licensed,
    };
    if (mode === "advanced") {
      Object.assign(p, {
        brand_guidelines: f.brand_guidelines || undefined, target_audience: f.target_audience || undefined,
        creator_id: f.creator_id || undefined, creator_prefs: Object.keys(prefs).length ? prefs : undefined,
        video_model: f.video_model || undefined, audio_mode: f.audio_mode, resolution: f.resolution,
        video_candidates: Number(f.video_candidates), keyframes: f.keyframes, subtitles: f.subtitles, end_card: f.end_card,
        music: f.music, approval_checkpoints: checkpoints,
        budget_credits: f.budget_credits ? Number(f.budget_credits) : undefined,
      });
    }
    return p;
  }, [f, mode, licensed]);

  useEffect(() => {
    const t = setTimeout(() => {
      post<Estimate>("/api/projects/estimate", payload).then((e) => { setEstimate(e); setEstErr(null); })
        .catch((e) => setEstErr(e.message));
    }, 400);
    return () => clearTimeout(t);
  }, [payload]);

  const hasInput = Boolean(f.product_url || f.product_description || images.length);

  async function submit(confirmBudget = false) {
    setBusy(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("payload", JSON.stringify({ ...payload, confirm_budget: confirmBudget }));
      images.forEach((img) => fd.append("images", img));
      const r = await post<{ project: ProjectSummary }>("/api/projects", fd);
      router.push(`/projects/${r.project.id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader title="New advertisement" description="Submit one product. The factory researches it, writes scripts, casts a creator, films, voices, edits and checks the ads."
        actions={<Tabs value={mode} onChange={setMode} tabs={[{ value: "simple", label: "Simple" }, { value: "advanced", label: "Advanced" }]} />} />
      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Product</CardTitle><CardDescription>Provide a URL, a description, images – or any combination.</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <Field label="Product URL" hint="Only publicly accessible pages; robots.txt is respected.">
                <Input type="url" placeholder="https://shop.example.com/product" value={f.product_url} onChange={(e) => set("product_url", e.target.value)} />
              </Field>
              <Field label="Product description" hint="Facts only – the ads never claim more than you state here or on the page.">
                <Textarea rows={4} value={f.product_description} onChange={(e) => set("product_description", e.target.value)}
                  placeholder="What it is, what it does, who it is for, price…" />
              </Field>
              <div className="grid gap-4 sm:grid-cols-3">
                <Field label="Product name"><Input value={f.product_name} onChange={(e) => set("product_name", e.target.value)} placeholder="as spoken in the ad" /></Field>
                <Field label="Brand name"><Input value={f.brand_name} onChange={(e) => set("brand_name", e.target.value)} /></Field>
                <Field label="Project name"><Input value={f.name} onChange={(e) => set("name", e.target.value)} placeholder="optional" /></Field>
              </div>
              <Field label="Product images" hint="Real photos are used to keep packaging, labels and logos exact (JPEG/PNG/WebP, ≤ 15 MB).">
                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed px-4 py-6 text-sm text-muted-foreground hover:bg-muted/50">
                  <ImagePlus className="h-4 w-4" /> Add images
                  <input type="file" accept="image/jpeg,image/png,image/webp" multiple className="hidden"
                    onChange={(e) => setImages((cur) => [...cur, ...Array.from(e.target.files ?? [])].slice(0, 8))} />
                </label>
                {images.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {images.map((img, i) => (
                      <div key={i} className="relative h-20 w-20 overflow-hidden rounded-md border">
                        <img src={URL.createObjectURL(img)} alt="" className="h-full w-full object-cover" />
                        <button type="button" onClick={() => setImages(images.filter((_, j) => j !== i))}
                          className="absolute right-1 top-1 rounded bg-background/80 p-0.5"><X className="h-3 w-3" /></button>
                      </div>
                    ))}
                  </div>
                )}
                {images.length > 0 && (
                  <label className="mt-2 flex items-start gap-2 text-xs">
                    <input type="checkbox" checked={licensed} onChange={(e) => setLicensed(e.target.checked)} className="mt-0.5" />
                    I own or am licensed to use these images for advertising.
                  </label>
                )}
              </Field>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Advertisement</CardTitle></CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <Field label="Language">
                <Select value={f.language} onChange={(e) => set("language", e.target.value as "en" | "de")}>
                  <option value="en">English</option><option value="de">Deutsch</option>
                </Select>
              </Field>
              <Field label="Number of variants">
                <Select value={f.variants} onChange={(e) => set("variants", Number(e.target.value))}>
                  {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
                </Select>
              </Field>
              <Field label={`Duration: ${f.duration}s`}>
                <input type="range" min={8} max={60} step={1} value={f.duration} onChange={(e) => set("duration", Number(e.target.value))} className="w-full accent-[hsl(var(--primary))]" />
              </Field>
              <Field label="Call to action"><Input value={f.cta} onChange={(e) => set("cta", e.target.value)} placeholder={f.language === "de" ? "Jetzt entdecken" : "Shop now"} /></Field>
            </CardContent>
          </Card>

          {mode === "advanced" && (
            <>
              <Card>
                <CardHeader><CardTitle>Audience & brand</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <Field label="Target audience"><Input value={f.target_audience} onChange={(e) => set("target_audience", e.target.value)} placeholder="e.g. busy parents in cities" /></Field>
                  <Field label="Brand guidelines"><Textarea rows={3} value={f.brand_guidelines} onChange={(e) => set("brand_guidelines", e.target.value)} placeholder="Tone, words to avoid, mandatory disclaimers…" /></Field>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Creator</CardTitle><CardDescription>Reuse a creator from the library for consistent identity, or describe a new fictional one.</CardDescription></CardHeader>
                <CardContent className="space-y-4">
                  <Field label="Creator">
                    <Select value={f.creator_id} onChange={(e) => set("creator_id", e.target.value)}>
                      <option value="">Generate a new fictional creator</option>
                      {creators.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </Select>
                  </Field>
                  {!f.creator_id && (
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field label="Gender presentation">
                        <Select value={f.gender} onChange={(e) => set("gender", e.target.value)}>
                          <option value="">Let the director decide</option><option value="female">Female</option><option value="male">Male</option><option value="any">Any</option>
                        </Select>
                      </Field>
                      <Field label="Age range"><Input value={f.age_range} onChange={(e) => set("age_range", e.target.value)} placeholder="25-34" /></Field>
                      <Field label="Appearance"><Input value={f.appearance} onChange={(e) => set("appearance", e.target.value)} placeholder="curly dark hair, glasses" /></Field>
                      <Field label="Clothing"><Input value={f.clothing} onChange={(e) => set("clothing", e.target.value)} placeholder="denim jacket" /></Field>
                      <div className="sm:col-span-2"><Field label="Environment"><Input value={f.environment} onChange={(e) => set("environment", e.target.value)} placeholder="bright home office" /></Field></div>
                    </div>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Production</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Field label="Video model" hint="Limits (duration, audio) are read from the LetzAI catalogue.">
                      <Select value={f.video_model} onChange={(e) => set("video_model", e.target.value)}>
                        <option value="">Default</option>
                        {videoModels.map((m) => (
                          <option key={m.key} value={m.key}>
                            {m.displayName} ({m.capabilities.video?.duration?.min}–{m.capabilities.video?.duration?.max}s{m.capabilities.video?.allowAudio ? ", audio" : ""})
                          </option>
                        ))}
                      </Select>
                    </Field>
                    <Field label="Audio">
                      <Select value={f.audio_mode} onChange={(e) => set("audio_mode", e.target.value)}>
                        <option value="auto">Auto (native when the model supports it)</option>
                        <option value="native">Native model audio</option>
                        <option value="tts">Speech synthesis</option>
                      </Select>
                    </Field>
                    <Field label="Resolution">
                      <Select value={f.resolution} onChange={(e) => set("resolution", e.target.value)}>
                        {["480p", "720p", "768p", "1080p"].map((r) => <option key={r}>{r}</option>)}
                      </Select>
                    </Field>
                    <Field label="Candidates per scene">
                      <Select value={f.video_candidates} onChange={(e) => set("video_candidates", Number(e.target.value))}>
                        {[1, 2, 3].map((n) => <option key={n} value={n}>{n}</option>)}
                      </Select>
                    </Field>
                    <Field label="Keyframes">
                      <Select value={f.keyframes} onChange={(e) => set("keyframes", e.target.value)}>
                        <option value="per_scene">Per scene (best consistency)</option>
                        <option value="anchor_only">Anchor only (cheaper)</option>
                      </Select>
                    </Field>
                    <Field label="Budget (credits)"><Input type="number" min={0} value={f.budget_credits} onChange={(e) => set("budget_credits", e.target.value)} placeholder="default" /></Field>
                  </div>
                  <Separator />
                  <div className="flex flex-wrap gap-x-6 gap-y-3">
                    <Switch checked={f.subtitles} onChange={(v) => set("subtitles", v)} label="Burned-in captions" />
                    <Switch checked={f.end_card} onChange={(v) => set("end_card", v)} label="End card" />
                    <Switch checked={f.music} onChange={(v) => set("music", v)} label="Background music" />
                  </div>
                  <Separator />
                  <div>
                    <div className="mb-2 text-sm font-medium">Approval checkpoints</div>
                    <p className="mb-3 text-xs text-muted-foreground">By default the pipeline runs autonomously. Pause for review at:</p>
                    <div className="flex flex-wrap gap-x-6 gap-y-3">
                      <Switch checked={f.cp_concepts} onChange={(v) => set("cp_concepts", v)} label="Concepts & scripts" />
                      <Switch checked={f.cp_creator} onChange={(v) => set("cp_creator", v)} label="Creator" />
                      <Switch checked={f.cp_storyboard} onChange={(v) => set("cp_storyboard", v)} label="Storyboard" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        <div className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Coins className="h-4 w-4" />Cost estimate</CardTitle>
              <CardDescription>{estimate?.basis ?? "Estimated before any paid request"}</CardDescription></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {estErr && <Alert variant="destructive">{estErr}</Alert>}
              {estimate && (
                <>
                  {estimate.lines.map((l) => (
                    <div key={l.item} className="flex justify-between gap-3">
                      <span className="text-muted-foreground">{l.item}{l.qty > 1 ? ` ×${l.qty}` : ""}</span>
                      <span className="tabular-nums">{fmtCredits(l.credits)}</span>
                    </div>
                  ))}
                  <Separator className="my-2" />
                  <div className="flex justify-between font-semibold"><span>Total</span><span className="tabular-nums">{fmtCredits(estimate.total_credits)} credits</span></div>
                  {estimate.usd != null && <div className="text-right text-xs text-muted-foreground">≈ ${estimate.usd}</div>}
                  <div className="pt-1 text-xs text-muted-foreground">{estimate.video_model} · {estimate.audio_mode} audio · ~{estimate.scenes_per_ad} scenes per ad</div>
                </>
              )}
            </CardContent>
          </Card>
          {error && <Alert variant="destructive">{error}</Alert>}
          <Button className="w-full" size="lg" disabled={!hasInput || busy || (images.length > 0 && !licensed)} onClick={() => submit(false)}>
            <Sparkles />{busy ? "Starting…" : "Generate advertisements"}
          </Button>
          {estimate && f.budget_credits && estimate.total_credits > Number(f.budget_credits) && (
            <Button variant="outline" className="w-full" disabled={busy} onClick={() => submit(true)}>Start and raise budget to estimate</Button>
          )}
          <p className="text-xs text-muted-foreground">Creators are fictional. Scripts never invent testimonials or personal results. If the estimate exceeds the budget, the project waits for your confirmation.</p>
        </div>
      </div>
    </>
  );
}
