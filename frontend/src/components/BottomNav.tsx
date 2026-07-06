import { Home, UserCircle2 } from "lucide-react";

interface BottomNavProps {
  active: "home" | "workout";
  onHome: () => void;
}

export function BottomNav({ active, onHome }: BottomNavProps) {
  const iconClass = (name: "home" | "workout") =>
    `h-6 w-6 ${active === name ? "text-cy-text" : "text-cy-muted"}`;

  return (
    <nav className="mt-4 grid grid-cols-2 gap-3 rounded-2xl bg-cy-surface/90 p-3">
      <button
        type="button"
        onClick={onHome}
        className="flex items-center justify-center rounded-full bg-cy-orange p-3 transition hover:scale-105"
        aria-label="Home"
      >
        <Home className={iconClass("home")} />
      </button>
      <button
        type="button"
        className="flex items-center justify-center rounded-full bg-cy-orange p-3 transition hover:scale-105"
        aria-label="Profile placeholder"
      >
        <UserCircle2 className="h-6 w-6 text-cy-text" />
      </button>
    </nav>
  );
}
