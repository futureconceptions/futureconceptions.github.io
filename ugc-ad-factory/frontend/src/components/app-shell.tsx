"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Clapperboard, Film, LayoutDashboard, LogOut, Plus, Settings, Users, Workflow } from "lucide-react";
import { api, getToken, setToken } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/new", label: "New Advertisement", icon: Plus },
  { href: "/projects", label: "Production Monitor", icon: Workflow },
  { href: "/library", label: "Ad Library", icon: Film },
  { href: "/creators", label: "Creator Library", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<{ email: string; role: string } | null>(null);
  const isLogin = pathname === "/login";

  useEffect(() => {
    if (isLogin) return;
    if (!getToken()) { router.replace("/login"); return; }
    api<{ email: string; role: string }>("/api/auth/me").then(setMe).catch(() => undefined);
  }, [isLogin, router]);

  if (isLogin) return <>{children}</>;
  if (!me) return <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">Loading…</div>;

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r bg-card md:flex">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"><Clapperboard className="h-4 w-4" /></div>
          <div>
            <div className="text-sm font-semibold leading-tight">UGC Ad Factory</div>
            <div className="text-[11px] text-muted-foreground">powered by LetzAI</div>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 px-3">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link key={href} href={href}
                className={cn("flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                  active ? "bg-accent font-medium text-accent-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground")}>
                <Icon className="h-4 w-4" />{label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t p-4 text-xs">
          <div className="truncate font-medium">{me.email}</div>
          <div className="mb-2 text-muted-foreground">{me.role}</div>
          <button className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => { setToken(null); router.replace("/login"); }}>
            <LogOut className="h-3.5 w-3.5" /> Sign out
          </button>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 overflow-x-auto border-b bg-card px-4 py-2 md:hidden">
          {NAV.map(({ href, icon: Icon, label }) => (
            <Link key={href} href={href} aria-label={label} className="rounded-md p-2 text-muted-foreground hover:bg-muted"><Icon className="h-4 w-4" /></Link>
          ))}
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-8 md:py-8">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
