export type IllustrativeRoundAnswer = "YES" | "NO" | "RATHER YES" | "RATHER NO" | "IDENTIFIED";

export interface IllustrativeRoundTurn {
  readonly kind: "question" | "guess";
  readonly prompt: string;
  readonly answer: IllustrativeRoundAnswer;
}

export interface IllustrativeRound {
  readonly category: string;
  readonly subject: string;
  readonly turns: readonly IllustrativeRoundTurn[];
}

export const illustrativeRound = {
  category: "Fictional character",
  subject: "Garfield",
  turns: [
    {
      kind: "question",
      prompt: "Is the character human?",
      answer: "NO",
    },
    {
      kind: "question",
      prompt: "Is it an animal?",
      answer: "YES",
    },
    {
      kind: "question",
      prompt: "Is it known for comic strips?",
      answer: "YES",
    },
    {
      kind: "guess",
      prompt: "Garfield",
      answer: "IDENTIFIED",
    },
  ],
} as const satisfies IllustrativeRound;

// An illustrative evidence gap, not a probability assigned to a known property.
export const qualifiedIllustrativeRound = {
  ...illustrativeRound,
  turns: [
    illustrativeRound.turns[0],
    illustrativeRound.turns[1],
    { kind: "question", prompt: "Do the sources mainly describe a comic-strip character?",
      answer: "RATHER YES" },
    illustrativeRound.turns[3],
  ],
} as const satisfies IllustrativeRound;
