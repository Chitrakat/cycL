import { useMemo } from "react";

interface HomeScreenProps {
  hasActiveWorkout: boolean;
  onOpenGenerate: () => void;
  onStartLive: () => void;
}

const projectHighlights = [
  {
    title: "What it is",
    body: "Cyc.ly turns workout preferences into a focused ride session so the next training block is always one tap away.",
  },
  {
    title: "How I made it",
    body: "The app pairs a React frontend with a Python backend, then uses workout data and simple generation rules to build each ride.",
  },
  {
    title: "Why it exists",
    body: "It removes decision fatigue before a ride and keeps the training experience fast, personal, and repeatable.",
  },
] as const;

const buildNotes = ["React UI", "TypeScript", "Tailwind styling", "Python workflow"] as const;

export function HomeScreen({ hasActiveWorkout, onOpenGenerate, onStartLive }: HomeScreenProps) {
  const weekday = useMemo(() => new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  }), []);

  return (
    <div className="space-y-4 lg:grid lg:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)] lg:gap-5 lg:space-y-0">
      <div className="space-y-4">
      <header className="rounded-2xl bg-transparent px-1 pt-2">
        <h1 className="text-stroke-soft text-5xl font-bold tracking-wide text-cy-text">Cyc.ly</h1>
        <p className="mt-2 text-sm uppercase tracking-[0.2em] text-cy-muted">{weekday}</p>
      </header>

      <section className="rounded-2xl bg-cy-surface p-3">
        <div className="rounded-xl bg-cy-card p-5">
          <p className="text-sm uppercase tracking-[0.24em] text-cy-orange">About this build</p>
          <h2 className="mt-2 text-4xl font-bold text-cy-text">A small system for building better rides</h2>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-cy-muted">
            Cyc.ly was built to make workout planning feel immediate. Instead of starting from a blank screen,
            the app assembles a ride experience from the training setup you choose and keeps the flow lightweight.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            {buildNotes.map((note) => (
              <span key={note} className="rounded-full border border-white/10 bg-black/30 px-3 py-1 text-sm text-cy-text">
                {note}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-2xl bg-cy-surface p-3">
        <h3 className="mb-3 text-4xl font-bold uppercase text-cy-text">Project story</h3>
        <div className="space-y-3">
          {projectHighlights.map((item) => (
            <div key={item.title} className="rounded-xl bg-cy-card p-4">
              <p className="text-sm uppercase tracking-[0.2em] text-cy-orange">{item.title}</p>
              <p className="mt-3 text-lg leading-7 text-cy-muted">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      </div>

      <section className="hidden rounded-2xl bg-cy-surface p-3 lg:block lg:sticky lg:top-4 lg:self-start">
        <div className="rounded-xl bg-cy-card p-4">
          <p className="text-sm uppercase tracking-[0.24em] text-cy-orange">Desktop launch panel</p>
          <h3 className="mt-2 text-3xl font-bold text-cy-text">Build, then launch</h3>
          <p className="mt-3 text-base leading-7 text-cy-muted">
            Generate a workout first, then open the active workout when the session is ready.
          </p>
          <button
            type="button"
            onClick={onOpenGenerate}
            className="mt-5 w-full rounded-full bg-[#181a1e] px-6 py-4 text-2xl font-medium text-cy-text transition hover:bg-black"
          >
            Generate Workout
          </button>
          <button
            type="button"
            onClick={onStartLive}
            disabled={!hasActiveWorkout}
            className={`mt-3 w-full rounded-full border px-6 py-3 text-lg font-medium transition ${hasActiveWorkout ? "border-cy-orange/40 bg-cy-orange/20 text-cy-orange hover:bg-cy-orange/30" : "cursor-not-allowed border-white/10 bg-white/5 text-cy-muted opacity-60"}`}
          >
            {hasActiveWorkout ? "Open Active Workout" : "Generate a workout first"}
          </button>
        </div>
      </section>

      <section className="rounded-2xl bg-cy-surface p-3 lg:hidden">
        <div className="rounded-xl bg-cy-card p-4">
          <button
            type="button"
            onClick={onOpenGenerate}
            className="w-full rounded-full bg-[#181a1e] px-6 py-4 text-3xl font-medium text-cy-text transition hover:bg-black"
          >
            Generate Workout
          </button>
          <button
            type="button"
            onClick={onStartLive}
            disabled={!hasActiveWorkout}
            className={`mt-3 w-full rounded-full border px-6 py-3 text-xl font-medium transition ${hasActiveWorkout ? "border-cy-orange/40 bg-cy-orange/20 text-cy-orange hover:bg-cy-orange/30" : "cursor-not-allowed border-white/10 bg-white/5 text-cy-muted opacity-60"}`}
          >
            {hasActiveWorkout ? "Open Active Workout" : "Generate a workout first"}
          </button>
        </div>
      </section>
    </div>
  );
}

export function TodayRideCard() {
  return (
    <div className="rounded-xl bg-cy-card p-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-bold text-cy-text">Today’s ride</h2>
          <p className="mt-3 text-xl text-cy-muted">Restore the ride summary here when you want it back.</p>
        </div>
        <div className="flex h-24 w-24 items-center justify-center rounded-full bg-cy-orange/30 text-5xl font-bold text-cy-orange shadow-neonOrange">
          6
        </div>
      </div>
    </div>
  );
}

export function OverviewPanel() {
  return (
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <div className="rounded-xl bg-cy-card p-3">
        <div className="flex items-center justify-between">
          <span className="text-lg text-cy-muted">Sessions</span>
          <span className="rounded-full bg-cy-orange px-2 text-sm text-black">Coming soon</span>
        </div>
        <div className="mt-4 flex h-36 items-center justify-center rounded-xl bg-black/35 text-cy-muted">
          Placeholder
        </div>
      </div>

      <div className="rounded-xl bg-cy-card p-3">
        <div className="flex items-center justify-between">
          <span className="text-lg text-cy-muted">Weekly Effort</span>
          <span className="rounded-full bg-cy-orange px-2 text-sm text-black">Coming soon</span>
        </div>
        <div className="mt-4 flex h-36 items-center justify-center rounded-xl bg-black/35 text-cy-muted">
          Placeholder
        </div>
      </div>
    </div>
  );
}
