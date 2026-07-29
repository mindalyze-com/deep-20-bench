export type IllustrativeRoundAnswer = "YES" | "NO" | "IDENTIFIED";

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
