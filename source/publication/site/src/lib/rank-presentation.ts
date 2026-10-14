import type { LeaderboardRow } from "./types";

export const rankPresentation = (
  row: LeaderboardRow,
  rows: readonly LeaderboardRow[],
): { tied: boolean; note: string } => {
  if (row.rank === null) return { tied: false, note: "Unranked" };
  const others = rows.filter((other) => other.model.model_id !== row.model.model_id);
  const tied = others.some((other) => other.rank === row.rank);
  const peers = others.filter((other) =>
    row.question_score !== null && other.question_score === row.question_score &&
    other.rank !== null && other.rank !== row.rank);
  const shared = tied ? `Shared rank ${row.rank}. ` : "";
  if (peers.length > 0 && row.question_score_confidence_interval === null) {
    return { tied, note: `${shared}Same average score; 95% CI unavailable.` };
  }
  if (peers.length === 1) {
    const peer = peers[0]!;
    if (peer.question_score_confidence_interval === null) {
      return { tied, note: `${shared}Same average score as rank ${peer.rank}; 95% CI available.` };
    }
    const direction = row.rank < peer.rank! ? "narrower" : "wider";
    return { tied, note: `${shared}Same average score as rank ${peer.rank}; ${direction} 95% CI.` };
  }
  return { tied, note: peers.length > 1
    ? `${shared}Same average score; rank decided by 95% CI width.`
    : tied ? `Shared rank ${row.rank}. Equal average score and 95% CI width.` : `Rank ${row.rank}` };
};

export const hasScoreTies = (rows: readonly LeaderboardRow[]): boolean =>
  rows.some((row, index) => row.question_score !== null && rows.slice(index + 1)
    .some((other) => other.question_score === row.question_score));
