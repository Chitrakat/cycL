import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { BottomNav } from "./components/BottomNav";
import { GenerateWorkoutModal } from "./components/GenerateWorkoutModal";
import { HomeScreen } from "./components/HomeScreen";
import { WorkoutScreen } from "./components/WorkoutScreen";
import { fetchDurations, fetchWorkoutTypes, generateWorkoutFromBackend } from "./lib/api";
import type { WorkoutPickerState, WorkoutSession } from "./types";

type Screen = "home" | "workout";

function createFallbackSession(picker: WorkoutPickerState): WorkoutSession {
  const baseByDifficulty = {
    easy: [2, 3, 4, 3],
    medium: [4, 5, 6, 5],
    hard: [6, 7, 8, 7],
  } as const;

  const seed = baseByDifficulty[picker.difficulty];
  const totalSeconds = picker.durationMinutes * 60;
  const segmentDuration = 30;
  const segmentCount = Math.max(1, Math.floor(totalSeconds / segmentDuration));
  const segments = Array.from({ length: segmentCount }, (_, index) => {
    const zone = seed[index % seed.length];
    return {
      zone,
      durationSeconds: segmentDuration,
      rpm: 62 + zone * 4,
    };
  });

  const powerProfile = segments.map((s) => s.zone / 10);

  return {
    id: Date.now(),
    workoutType: picker.workoutType,
    durationMinutes: picker.durationMinutes,
    ftp: picker.difficulty === "easy" ? 180 : picker.difficulty === "medium" ? 240 : 290,
    fitnessLevel: picker.difficulty === "easy" ? "beginner" : picker.difficulty === "medium" ? "intermediate" : "advanced",
    powerProfile,
    segments,
  };
}

function App() {
  const [screen, setScreen] = useState<Screen>("home");
  const [modalOpen, setModalOpen] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [types, setTypes] = useState<string[]>(["HIIT"]);
  const [durations, setDurations] = useState<number[]>([30]);
  const [elapsed, setElapsed] = useState(70);
  const [paused, setPaused] = useState(false);

  const [picker, setPicker] = useState<WorkoutPickerState>({
    durationMinutes: 30,
    workoutType: "HIIT",
    difficulty: "medium",
  });

  const [session, setSession] = useState<WorkoutSession | null>(null);

  useEffect(() => {
    fetchWorkoutTypes().then((list) => {
      if (!list.length) return;
      setTypes(list);
      setPicker((prev) => ({ ...prev, workoutType: list[0] }));
    });
  }, []);

  useEffect(() => {
    fetchDurations(picker.workoutType).then((list) => {
      if (!list.length) return;
      setDurations(list);
      setPicker((prev) => {
        if (list.includes(prev.durationMinutes)) {
          return prev;
        }

        const closest = list.reduce((best, value) => {
          const bestDiff = Math.abs(best - prev.durationMinutes);
          const currentDiff = Math.abs(value - prev.durationMinutes);
          return currentDiff < bestDiff ? value : best;
        }, list[0]);

        return { ...prev, durationMinutes: closest };
      });
    });
  }, [picker.workoutType]);

  useEffect(() => {
    if (screen !== "workout" || paused || !session) return;
    if (elapsed >= session.durationMinutes * 60) return;
    const timer = window.setInterval(() => {
      setElapsed((s) => s + 1);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [screen, paused, session, elapsed]);

  const handleSkipZone = (secondsToSkip: number) => {
    if (!session || secondsToSkip <= 0) return;

    const totalSeconds = session.durationMinutes * 60;
    setElapsed((current) => Math.min(current + secondsToSkip, totalSeconds));
  };

  const handleGenerate = async () => {
    try {
      setLoadingGenerate(true);
      const generated = await generateWorkoutFromBackend(
        picker.workoutType,
        picker.durationMinutes,
        picker.difficulty,
      );
      setSession(generated);
    } catch {
      setSession(createFallbackSession(picker));
    } finally {
      setElapsed(0);
      setPaused(false);
      setScreen("workout");
      setModalOpen(false);
      setLoadingGenerate(false);
    }
  };

  const appShellClass = useMemo(
    () =>
      "mx-auto min-h-screen w-full max-w-[1200px] px-3 py-4 md:px-8",
    [],
  );

  return (
    <div className={appShellClass}>
      <main className="mx-auto w-full max-w-[420px] rounded-[34px] border border-white/15 bg-black/60 p-4 shadow-[0_0_0_2px_rgba(255,255,255,0.09),0_30px_60px_rgba(0,0,0,0.45)] lg:max-w-none lg:rounded-[40px] lg:p-6">
        {screen === "home" ? (
          <HomeScreen
            hasActiveWorkout={session !== null}
            onOpenGenerate={() => setModalOpen(true)}
            onStartLive={() => {
              if (session) {
                setScreen("workout");
              }
            }}
          />
        ) : (
          <WorkoutScreen
            session={session}
            elapsedSeconds={elapsed}
            paused={paused}
            onSkipZone={handleSkipZone}
            onTogglePause={() => setPaused((value) => !value)}
          />
        )}

        <BottomNav active={screen} onHome={() => setScreen("home")} />
      </main>

      <GenerateWorkoutModal
        open={modalOpen}
        loading={loadingGenerate}
        state={picker}
        durations={durations}
        types={types}
        onClose={() => setModalOpen(false)}
        onStateChange={setPicker}
        onGenerate={handleGenerate}
      />
    </div>
  );
}

export default App;
