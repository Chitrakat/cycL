import { useMemo } from "react";
import type { ZoneColor } from "../types";
import { themeByZoneColor } from "../lib/zone";

interface WorkoutOrbProps {
  zone: number;
  zoneColor: ZoneColor;
  rpm: number;
  paused: boolean;
}

export function WorkoutOrb({ zone, zoneColor, rpm, paused }: WorkoutOrbProps) {
  const theme = themeByZoneColor(zoneColor);

  const dashOffset = useMemo(() => {
    // Higher RPM rotates the indicator faster via CSS animation duration,
    // while this creates a subtle static shift to prevent visual lock.
    return (rpm % 100) / 100;
  }, [rpm]);

  const animDuration = 60 / Math.max(rpm, 1);

  return (
    <div className="relative mx-auto mt-4 h-56 w-56">
      <div
        className="absolute inset-0 rounded-full"
        style={{ backgroundColor: theme.ring2 }}
      />
      <div
        className="absolute left-5 top-5 h-46 w-46 rounded-full"
        style={{ backgroundColor: theme.ring1 }}
      />

      <div
        className="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full text-center text-6xl font-bold leading-[7rem] text-white"
        style={{ backgroundColor: theme.core }}
      >
        {zone}
      </div>

      <div
        className="absolute inset-0"
        style={{ animation: `spin ${animDuration}s linear infinite`, animationPlayState: paused ? "paused" : "running" }}
      >
        <span
          className="absolute left-1/2 top-[18px] block h-5 w-[6px] -translate-x-1/2 rounded-full bg-white"
          style={{ opacity: 0.95 - dashOffset * 0.25 }}
        />
        <span className="absolute bottom-[18px] left-1/2 block h-5 w-[6px] -translate-x-1/2 rounded-full bg-white" />
      </div>
    </div>
  );
}
