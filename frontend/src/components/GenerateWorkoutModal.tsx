import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Difficulty, WorkoutPickerState } from "../types";

interface GenerateWorkoutModalProps {
  open: boolean;
  loading: boolean;
  state: WorkoutPickerState;
  durations: number[];
  types: string[];
  onClose: () => void;
  onStateChange: (next: WorkoutPickerState) => void;
  onGenerate: () => void;
}

const difficulties: { key: Difficulty; label: string; color: string }[] = [
  { key: "easy", label: "Easy", color: "#62B30F" },
  { key: "medium", label: "Medium", color: "#FFD21F" },
  { key: "hard", label: "Hard", color: "#FF3B43" },
];

export function GenerateWorkoutModal({
  open,
  loading,
  state,
  durations,
  types,
  onClose,
  onStateChange,
  onGenerate,
}: GenerateWorkoutModalProps) {
  if (!open) return null;

  const durationIndex = Math.max(durations.indexOf(state.durationMinutes), 0);
  const typeIndex = Math.max(types.indexOf(state.workoutType), 0);

  const shiftDuration = (delta: -1 | 1) => {
    if (!durations.length) return;
    const next = (durationIndex + delta + durations.length) % durations.length;
    onStateChange({ ...state, durationMinutes: durations[next] });
  };

  const shiftType = (delta: -1 | 1) => {
    if (!types.length) return;
    const next = (typeIndex + delta + types.length) % types.length;
    onStateChange({ ...state, workoutType: types[next] });
  };

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/55 p-4 sm:items-center">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-cy-card p-4 shadow-2xl">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-bold text-cy-text">Generate Workout</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-white/20 px-2 py-1 text-sm text-cy-muted"
          >
            Close
          </button>
        </div>

        <div className="space-y-3 rounded-xl bg-cy-surface p-3">
          <div className="flex items-center justify-between rounded-full bg-[#1f2125] px-2 py-2">
            <button
              type="button"
              onClick={() => shiftDuration(-1)}
              className="rounded-full bg-cy-orange p-2 text-black"
              aria-label="Previous duration"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-xl font-medium tracking-wide">{state.durationMinutes} mins</span>
            <button
              type="button"
              onClick={() => shiftDuration(1)}
              className="rounded-full bg-cy-orange p-2 text-black"
              aria-label="Next duration"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          <div className="flex items-center justify-between rounded-full bg-[#1f2125] px-2 py-2">
            <button
              type="button"
              onClick={() => shiftType(-1)}
              className="rounded-full bg-cy-orange p-2 text-black"
              aria-label="Previous workout type"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-2xl font-medium">{state.workoutType}</span>
            <button
              type="button"
              onClick={() => shiftType(1)}
              className="rounded-full bg-cy-orange p-2 text-black"
              aria-label="Next workout type"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          <div className="mt-4 flex overflow-hidden rounded-2xl bg-[#26282d] p-2">
            {difficulties.map((d) => {
              const selected = d.key === state.difficulty;
              return (
                <button
                  key={d.key}
                  type="button"
                  onClick={() => onStateChange({ ...state, difficulty: d.key })}
                  className={`flex-1 rounded-full px-3 py-8 text-lg transition ${selected ? "shadow-2xl" : "bg-[#3a3d44] text-cy-muted opacity-90"}`}
                  style={selected ? { backgroundColor: d.color, color: "#101010" } : undefined}
                >
                  {d.label}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            onClick={onGenerate}
            disabled={loading}
            className="mt-2 w-full rounded-full bg-cy-orange px-4 py-3 text-lg font-bold text-black transition hover:brightness-110 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Start Workout"}
          </button>
        </div>
      </div>
    </div>
  );
}
