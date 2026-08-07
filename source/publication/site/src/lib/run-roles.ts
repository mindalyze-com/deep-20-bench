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
    description: "Asks the questions and submits the scored guess.",
  },
  oracle: {
    costLabel: "Primary Oracle",
    roleLabel: "Primary Oracle",
    description: "Searches for evidence and proposes an answer.",
  },
  reviewer: {
    costLabel: "Reviewer",
    roleLabel: "Reviewer",
    description: "Checks each Oracle YES or NO independently.",
  },
  judge: {
    costLabel: "Judge",
    roleLabel: "Judge",
    description: "Decides when the Oracle and Reviewer disagree.",
  },
  validator: {
    costLabel: "Validator",
    roleLabel: "Guess Validator",
    description: "Checks a submitted guess against the trusted subject.",
  },
};

export const runRoleOrder: readonly PublicRunModel["role"][] = [
  "guesser",
  "oracle",
  "reviewer",
  "judge",
  "validator",
];
