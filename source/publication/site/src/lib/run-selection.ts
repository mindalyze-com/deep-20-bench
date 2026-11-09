import { date } from "./format";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
export const runDate = (value: string | null | undefined): string => value ? date(value) : "Date unavailable";
export const runLabel = (name: string, date: string | null | undefined): string => `${name} · ${runDate(date)}`;
export const useRunSelection = () => {
  const route = useRoute(); const router = useRouter();
  const allRuns = computed(() => route.query.history === "all");
  const select = (all: boolean) => { void router.push({ query: { ...route.query, history: all ? "all" : undefined } }); };
  return { allRuns, select };
};
