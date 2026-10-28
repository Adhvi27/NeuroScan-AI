import { NavLink } from "react-router-dom";
import { Brain, Menu, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const links = [
  { to: "/", label: "Home" },
  { to: "/analyze", label: "Analyze MRI" },
  { to: "/results", label: "Segmentation Results" },
  { to: "/visualize", label: "3D Visualization" },
  { to: "/performance", label: "Model Performance" },
  { to: "/about", label: "About" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-emerald-900/30 bg-gradient-to-r from-emerald-950 via-emerald-900 to-emerald-950 text-emerald-50 shadow-lg">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:px-6">
        <NavLink to="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 ring-1 ring-emerald-400/30">
            <Brain className="h-5 w-5 text-emerald-200" />
          </span>
          <span>
            NeuroScan <span className="text-emerald-300">AI</span>
          </span>
        </NavLink>
        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                cn(
                  "rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive ? "bg-emerald-800/80 text-white" : "text-emerald-100/90 hover:bg-emerald-800/50",
                )
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>
      {open && (
        <div className="border-t border-emerald-800/60 px-4 py-3 md:hidden">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              onClick={() => setOpen(false)}
              className="block rounded-lg px-3 py-2 text-sm hover:bg-emerald-800/50"
            >
              {l.label}
            </NavLink>
          ))}
        </div>
      )}
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mt-auto border-t border-emerald-100 bg-white/80">
      <div className="mx-auto max-w-7xl px-4 py-8 text-sm text-slate-600 md:px-6">
        <p className="font-medium text-emerald-900">NeuroScan AI — Research Prototype</p>
        <p className="mt-2 max-w-3xl leading-relaxed">
          For educational and research use only. Not FDA-cleared and not intended for clinical
          diagnosis or treatment decisions. Always consult qualified medical professionals.
        </p>
        <p className="mt-3 text-xs text-slate-500">© {new Date().getFullYear()} NeuroScan AI Project</p>
      </div>
    </footer>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-emerald-50/80 via-white to-emerald-50/40">
      <Navbar />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 md:px-6">{children}</main>
      <Footer />
    </div>
  );
}
