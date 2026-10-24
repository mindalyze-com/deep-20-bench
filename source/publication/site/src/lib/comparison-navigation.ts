import type { LocationQuery, Router } from "vue-router";

export const isComparisonDetail = (name: string | symbol | undefined): boolean =>
  name === "model" || name === "run" || name === "subject" || name === "episode";

export interface ComparisonScrollPosition {
  readonly top: number;
  readonly main: number;
  readonly subjects: number;
}

// Keep positions outside the view: its parent recreates nested content after a drilldown.
// Only this tab's UI positions are stored. Server renders never read or write them.
const scrollPositions = new Map<string, ComparisonScrollPosition>();
const storageKey = "deep20:comparison-scroll:v1";
const maximumPositions = 50;
let restored = false;
const validPosition = (value: unknown): value is ComparisonScrollPosition => {
  if (typeof value !== "object" || value === null) return false;
  return ["top", "main", "subjects"].every(key => {
    const coordinate = (value as Record<string, unknown>)[key];
    return typeof coordinate === "number" && Number.isFinite(coordinate) && coordinate >= 0;
  });
};
const restorePositions = (): void => {
  if (restored || typeof window === "undefined") return;
  restored = true;
  try {
    const stored = window.sessionStorage.getItem(storageKey);
    if (stored === null || stored.length > 256_000) return;
    const entries: unknown = JSON.parse(stored);
    if (!Array.isArray(entries)) return;
    for (const entry of entries.slice(-maximumPositions)) {
      if (Array.isArray(entry) && entry.length === 2 && typeof entry[0] === "string" &&
          entry[0].startsWith("/") && entry[0].length <= 4096 && validPosition(entry[1])) {
        const { top, main, subjects } = entry[1];
        scrollPositions.set(entry[0], { top, main, subjects });
      }
    }
  } catch { /* Storage can be unavailable; same-document navigation still uses memory. */ }
};
export const rememberComparisonScroll = (path: string, position: ComparisonScrollPosition): void => {
  if (typeof window === "undefined") return;
  restorePositions();
  if (path.length > 4096 || !validPosition(position)) return;
  scrollPositions.delete(path);
  scrollPositions.set(path, { ...position });
  if (scrollPositions.size > maximumPositions) scrollPositions.delete(scrollPositions.keys().next().value!);
  try { window.sessionStorage.setItem(storageKey, JSON.stringify([...scrollPositions])); }
  catch { /* Keep the in-memory position when storage is denied or full. */ }
};
export const comparisonScroll = (path: string): ComparisonScrollPosition | null => {
  if (typeof window === "undefined") return null;
  restorePositions();
  return scrollPositions.get(path) ?? null;
};

/** Only a local comparison route may be used as a return destination. */
export const comparisonReturnPath = (router: Router, query: LocationQuery): string | null => {
  const candidate = query.compare;
  if (typeof candidate !== "string" || candidate.length > 4096 ||
      !candidate.startsWith("/") || candidate.startsWith("//") || candidate.includes("\\")) return null;
  try {
    const destination = router.resolve(candidate);
    return destination.name === "results-compare" ? destination.fullPath : null;
  } catch {
    return null;
  }
};
