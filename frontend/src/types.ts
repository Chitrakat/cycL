export type Difficulty = "easy" | "medium" | "hard";

export type ZoneColor = "green" | "orange" | "red";

export interface WorkoutPickerState {
  durationMinutes: number;
  workoutType: string;
  difficulty: Difficulty;
}

export interface WorkoutSession {
  id: number;
  workoutType: string;
  durationMinutes: number;
  ftp: number;
  fitnessLevel: "beginner" | "intermediate" | "advanced";
  powerProfile: number[];
  segments: WorkoutSegment[];
}

export interface WorkoutSegment {
  zone: number;
  durationSeconds: number;
  rpm: number;
}
