import type { WorkoutSegment, WorkoutSession } from "../types";

const API_BASE = "http://localhost:8000/api/v1/workouts";

interface TypesResponse {
  types: string[];
}

interface DurationsResponse {
  durations: number[];
}

interface GeneratePayload {
  template_id: number;
  ftp: number;
  fitness_level: "beginner" | "intermediate" | "advanced";
}

const fallbackTypes = ["HIIT", "Zone 2", "Power", "VO2max", "Sweet Spot", "Cadence"];

const fallbackDurations: Record<string, number[]> = {
  HIIT: [20, 25, 30, 35, 40, 45],
  "Zone 2": [30, 35, 45],
  Power: [25, 30],
  VO2max: [30, 33],
  "Sweet Spot": [30],
  Cadence: [25],
};

export async function fetchWorkoutTypes(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/types`);
    if (!res.ok) throw new Error("Failed to load workout types");
    const json = (await res.json()) as TypesResponse;
    return json.types;
  } catch {
    return fallbackTypes;
  }
}

export async function fetchDurations(workoutType: string): Promise<number[]> {
  try {
    const q = encodeURIComponent(workoutType);
    const res = await fetch(`${API_BASE}/durations?workout_type=${q}`);
    if (!res.ok) throw new Error("Failed to load durations");
    const json = (await res.json()) as DurationsResponse;
    return json.durations;
  } catch {
    return fallbackDurations[workoutType] ?? [30];
  }
}

export async function generateWorkoutFromBackend(
  workoutType: string,
  durationMinutes: number,
  difficulty: "easy" | "medium" | "hard",
): Promise<WorkoutSession> {
  const fit = difficulty === "easy" ? "beginner" : difficulty === "medium" ? "intermediate" : "advanced";
  const ftp = difficulty === "easy" ? 180 : difficulty === "medium" ? 240 : 290;

  const templateId = await findTemplateId(workoutType, durationMinutes);
  const payload: GeneratePayload = {
    template_id: templateId,
    ftp,
    fitness_level: fit,
  };

  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error("Failed to generate workout");
  }

  const json = await res.json();
  const segments = normalizeSegments(json.segments);
  const powerProfile =
    segments.length > 0
      ? segments.map((s) => s.zone / 10)
      : Array.isArray(json.power_profile)
        ? json.power_profile
        : [0.3, 0.4, 0.5, 0.6];

  return {
    id: json.id,
    workoutType: json.workout_type,
    durationMinutes: json.duration_minutes,
    ftp: json.ftp,
    fitnessLevel: json.fitness_level,
    powerProfile,
    segments,
  };
}

function normalizeSegments(input: unknown): WorkoutSegment[] {
  if (!Array.isArray(input)) return [];

  return input
    .map((raw): WorkoutSegment | null => {
      if (!raw || typeof raw !== "object") return null;
      const segment = raw as Record<string, unknown>;

      const durationSeconds =
        typeof segment.duration_seconds === "number"
          ? Math.max(1, Math.round(segment.duration_seconds))
          : typeof segment.duration === "number"
            ? Math.max(1, Math.round(segment.duration))
            : 8;

      const powerLevel = segment.power_level;
      const zone = parseZone(powerLevel);
      const rpm =
        typeof segment.cadence === "number"
          ? Math.max(40, Math.round(segment.cadence))
          : 62 + zone * 4;

      return {
        zone,
        durationSeconds,
        rpm,
      };
    })
    .filter((s): s is WorkoutSegment => Boolean(s));
}

function parseZone(power: unknown): number {
  if (typeof power === "number") {
    const n = Math.round(power * 10);
    return Math.min(10, Math.max(1, n));
  }

  if (typeof power === "string") {
    if (power.includes("/")) {
      const [n, d] = power.split("/").map((part) => Number(part));
      if (Number.isFinite(n) && Number.isFinite(d) && d > 0) {
        return Math.min(10, Math.max(1, Math.round((n / d) * 10)));
      }
    }

    const parsed = Number(power);
    if (Number.isFinite(parsed)) {
      return Math.min(10, Math.max(1, Math.round(parsed * 10)));
    }
  }

  return 4;
}

async function findTemplateId(workoutType: string, durationMinutes: number): Promise<number> {
  // Temporary strategy: use known working HIIT 30 template if not found.
  // The current backend does not expose a template list endpoint yet.
  if (workoutType === "HIIT" && durationMinutes === 30) {
    return 4;
  }

  // Fallback to known IDs based on seeded order.
  if (workoutType === "Power") return durationMinutes <= 25 ? 1 : 2;
  if (workoutType === "HIIT") return 4;
  if (workoutType === "Cadence") return 14;
  if (workoutType === "Sweet Spot") return 15;
  if (workoutType === "VO2max") return 16;
  if (workoutType === "Zone 2") return 18;

  return 4;
}
