import { cn } from "@/lib/utils";

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-emerald-100">
      <div
        className="h-full rounded-full bg-emerald-600 transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "h-8 w-8 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600",
        className,
      )}
    />
  );
}
