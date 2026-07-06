import { Pause, Play, SkipForward } from "lucide-react";
import { useMemo } from "react";
import { parseZoneFromPower, themeByZoneColor, zoneColorFromLevel } from "../lib/zone";
import type { WorkoutSession } from "../types";
import { WorkoutOrb } from "./WorkoutOrb";

interface WorkoutScreenProps {
  session: WorkoutSession | null;
  elapsedSeconds: number;
  paused: boolean;
  onSkipZone: (secondsToSkip: number) => void;
  onTogglePause: () => void;
}

function toClock(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function WorkoutScreen({ session, elapsedSeconds, paused, onSkipZone, onTogglePause }: WorkoutScreenProps) {
  const stats = useMemo(() => {
    if (!session) {
      return {
        zone: 4,
        nextZone: 5,
        zoneRemaining: 30,
        workoutRemaining: 30 * 60,
        rpm: 75,
      };
    }

    const totalSeconds = Math.max(1, session.durationMinutes * 60);
    const workoutElapsed = Math.min(elapsedSeconds, totalSeconds);

    if (session.segments.length) {
      let cursor = 0;
      let currentIndex = 0;

      for (let i = 0; i < session.segments.length; i += 1) {
        const segmentEnd = cursor + session.segments[i].durationSeconds;
        if (workoutElapsed < segmentEnd) {
          currentIndex = i;
          break;
        }
        cursor = segmentEnd;
        currentIndex = Math.min(i + 1, session.segments.length - 1);
      }

      const current = session.segments[currentIndex];
      const next = session.segments[Math.min(currentIndex + 1, session.segments.length - 1)];
      const segmentElapsed = Math.max(0, workoutElapsed - cursor);
      const zoneRemaining = Math.max(0, current.durationSeconds - segmentElapsed);
      const workoutRemaining = Math.max(0, totalSeconds - workoutElapsed);

      return {
        zone: current.zone,
        nextZone: next.zone,
        zoneRemaining,
        workoutRemaining,
        rpm: current.rpm,
      };
    }

    const index = Math.min(Math.floor(elapsedSeconds / 8), session.powerProfile.length - 1);
    const currentZone = parseZoneFromPower(session.powerProfile[index]);
    const nextZone = parseZoneFromPower(session.powerProfile[Math.min(index + 1, session.powerProfile.length - 1)]);
    const workoutRemaining = Math.max(0, session.durationMinutes * 60 - elapsedSeconds);
    const rpm = 62 + currentZone * 6;

    return {
      zone: currentZone,
      nextZone,
      zoneRemaining: Math.max(0, 8 - (elapsedSeconds % 8)),
      workoutRemaining,
      rpm,
    };
  }, [elapsedSeconds, session]);

  const zoneColor = zoneColorFromLevel(stats.zone);
  const theme = themeByZoneColor(zoneColor);

  return (
    <div className="rounded-2xl bg-black p-4 lg:p-6">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(280px,340px)_minmax(0,1fr)] lg:items-start">
        <div>
          <div className={`mx-auto w-[230px] rounded-xl border border-white/10 bg-black py-2 text-center text-sm tracking-[0.2em] text-cy-muted ${theme.glowClass}`}>
            NEXT ZONE: {stats.nextZone}
          </div>

          <WorkoutOrb zone={stats.zone} zoneColor={zoneColor} rpm={stats.rpm} />
        </div>

        <div className="space-y-4">
          <div className="rounded-xl bg-cy-surface p-3">
            <div className="rounded-xl bg-cy-card p-4 text-center">
              <p className="text-6xl font-bold text-cy-text">{toClock(stats.zoneRemaining)}</p>
              <p className="mt-1 text-sm tracking-[0.2em] text-cy-muted">TIME IN ZONE</p>
              <p className="mt-4 text-4xl text-cy-text">{toClock(stats.workoutRemaining)}</p>
              <p className="text-sm tracking-[0.2em] text-cy-muted">TIME REMAINING</p>
              <p className="mt-5 text-3xl font-bold" style={{ color: theme.core }}>RPM {stats.rpm}</p>
            </div>
          </div>

          <div className="flex items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => onSkipZone(stats.zoneRemaining)}
              className="flex items-center gap-2 rounded-full bg-cy-orange px-5 py-4 text-black transition hover:brightness-110"
              aria-label="Skip current zone"
            >
              <SkipForward className="h-6 w-6" />
              <span className="text-sm font-bold uppercase tracking-[0.18em]">Skip Zone</span>
            </button>
            <button
              type="button"
              onClick={onTogglePause}
              className="rounded-full bg-cy-orange p-4 text-black transition hover:brightness-110"
              aria-label={paused ? "Resume workout" : "Pause workout"}
            >
              {paused ? <Play className="h-7 w-7" /> : <Pause className="h-7 w-7" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
