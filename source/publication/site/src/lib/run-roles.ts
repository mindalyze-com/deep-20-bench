import type { PublicRunModel } from "./types";

export interface RunRoleCopy {
  readonly costLabel: string;
  readonly roleLabel: string;
  readonly description: string;
}

export const runRoleCopy: Readonly<Record<PublicRunModel["role"], RunRoleCopy>> = {
  guesser: {
    costLabel: "Guesser",
    roleLabel: "Guesser",
    description: "The tested model. Asks questions and makes guesses.",
  },
  oracle: {
    costLabel: "Primary Oracle",
    roleLabel: "Primary Oracle",
    description: "Searches for evidence and proposes an answer.",
  },
  reviewer: {
    costLabel: "Reviewer",
    roleLabel: "Reviewer",
    description: "Checks each Oracle answer except Unknown, without seeing it.",
  },
  judge: {
    costLabel: "Judge",
    roleLabel: "Judge",
    description: "Decides when the Oracle and Reviewer disagree.",
  },
  validator: {
    costLabel: "Validator",
    roleLabel: "Guess Validator",
    description: "Checks whether a guess names the hidden subject.",
  },
};

export const runRoleOrder: readonly PublicRunModel["role"][] = [
  "guesser",
  "oracle",
  "reviewer",
  "judge",
  "validator",
];
