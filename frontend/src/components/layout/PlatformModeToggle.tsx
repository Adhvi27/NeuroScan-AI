import { GraduationCap, Stethoscope } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSession, type PlatformMode } from "@/context/SessionContext";

export function PlatformModeToggle({ className }: { className?: string }) {
  const { platformMode, setPlatformMode } = useSession();

  const btn = (mode: PlatformMode, label: string, Icon: typeof GraduationCap) => (
    <button
      type="button"
      onClick={() => setPlatformMode(mode)}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors",
        platformMode === mode
          ? mode === "clinical"
            ? "bg-sky-600 text-white"
            : "bg-emerald-600 text-white"
          : "bg-black/20 text-emerald-100/80 hover:bg-black/30",
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </button>
  );

  return (
    <div className="flex items-center gap-1 rounded-xl bg-emerald-950/50 p-1 ring-1 ring-emerald-700/40">
      {btn("education", "Learning", GraduationCap)}
      {btn("clinical", "Clinical", Stethoscope)}
    </div>
  );
}

export function PlatformModeBanner() {
  const { platformMode } = useSession();
  if (platformMode === "education") {
    return (
      <p className="rounded-lg border border-emerald-800/50 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-100/90">
        <span className="font-semibold text-emerald-300">Learning mode</span> — explainer steps, curriculum,
        and demo fallbacks allowed. Not for patient care.
      </p>
    );
  }
  return (
    <p className="rounded-lg border border-sky-800/60 bg-sky-950/50 px-3 py-2 text-xs text-sky-100/90">
      <span className="font-semibold text-sky-300">Clinical workstation</span> — MSD-trained organ models only;
      no demo fallbacks. Assistive output — radiologist sign-off required.
    </p>
  );
}
