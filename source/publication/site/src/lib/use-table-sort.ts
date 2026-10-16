import { computed, ref, type Ref } from "vue";

import type { LeaderboardRow } from "./types";

export type SortDirection = "ascending" | "descending";
export type SortValue = number | string | null | undefined;

export interface TableSort {
  key: string;
  direction: SortDirection;
}

/**
 * Click-to-sort for result tables. The first click sorts ascending (lower is better for
 * most measures), the second descending, and the third restores the published order.
 * Missing values always sort last.
 */
export const useTableSort = <Row>(
  rows: Readonly<Ref<readonly Row[]>>,
  accessors: Readonly<Record<string, (row: Row) => SortValue>>,
) => {
  const sort = ref<TableSort | null>(null);

  const sortedRows = computed<readonly Row[]>(() => {
    const current = sort.value;
    const accessor = current === null ? undefined : accessors[current.key];
    if (current === null || accessor === undefined) return rows.value;
    const factor = current.direction === "ascending" ? 1 : -1;
    return rows.value
      .map((row, index) => ({ row, index, value: accessor(row) }))
      .sort((left, right) => {
        const leftMissing = left.value === null || left.value === undefined || left.value === "";
        const rightMissing = right.value === null || right.value === undefined || right.value === "";
        if (leftMissing || rightMissing) {
          return leftMissing === rightMissing ? left.index - right.index : leftMissing ? 1 : -1;
        }
        const order =
          typeof left.value === "number" && typeof right.value === "number"
            ? left.value - right.value
            : String(left.value).localeCompare(String(right.value));
        return order * factor || left.index - right.index;
      })
      .map((entry) => entry.row);
  });

  const toggleSort = (key: string): void => {
    const current = sort.value;
    if (current === null || current.key !== key) {
      sort.value = { key, direction: "ascending" };
    } else if (current.direction === "ascending") {
      sort.value = { key, direction: "descending" };
    } else {
      sort.value = null;
    }
  };

  const ariaSort = (key: string): "ascending" | "descending" | "none" =>
    sort.value?.key === key ? sort.value.direction : "none";

  return { sort, sortedRows, toggleSort, ariaSort };
};

const numeric = (value: string | number | null | undefined): number | null =>
  value === null || value === undefined || value === "" ? null : Number(value);

/** Sort keys shared by the leaderboard tables; keys match the table column keys. */
export const leaderboardSortAccessors: Readonly<
  Record<string, (row: LeaderboardRow) => SortValue>
> = {
  model: (row) => row.model.display_name,
  score: (row) => numeric(row.question_score),
  reasoning: (row) => row.model.reasoning_effort,
  success: (row) => numeric(row.success_rate),
  contract: (row) => numeric(row.contract?.compliance_rate),
  cost: (row) => numeric(row.guesser_cost_per_episode_usd),
  "run-cost": (row) => numeric(row.total_cost_usd),
  time: (row) => numeric(row.guesser_think_time_per_episode_ms),
};
