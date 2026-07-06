import type { ZoneColor } from "../types";

export function zoneColorFromLevel(zone: number): ZoneColor {
  if (zone <= 3) return "green";
  if (zone <= 6) return "orange";
  return "red";
}

export function themeByZoneColor(zoneColor: ZoneColor) {
  if (zoneColor === "green") {
    return {
      core: "#62B30F",
      ring1: "rgba(98,179,15,0.45)",
      ring2: "rgba(98,179,15,0.25)",
      glowClass: "shadow-neonGreen",
    };
  }

  if (zoneColor === "orange") {
    return {
      core: "#FF9727",
      ring1: "rgba(255,151,39,0.45)",
      ring2: "rgba(255,151,39,0.25)",
      glowClass: "shadow-neonOrange",
    };
  }

  return {
    core: "#FF3B43",
    ring1: "rgba(255,59,67,0.45)",
    ring2: "rgba(255,59,67,0.25)",
    glowClass: "shadow-neonRed",
  };
}

export function parseZoneFromPower(value: number): number {
  const scaled = Math.round(value * 10);
  if (scaled < 1) return 1;
  if (scaled > 10) return 10;
  return scaled;
}
