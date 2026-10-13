import type { PublicContractViolationTurn } from "./types";

export interface ContractViolationDetail {
  label: string;
  description: string;
}

export const contractViolationDetails = {
  invalid_json: {
    label: "Invalid JSON",
    description: "The reply was not one complete, valid JSON object.",
  },
  invalid_action: {
    label: "Invalid action",
    description:
      "The reply was JSON, but it matched neither the ASK nor the GUESS format.",
  },
  output_limit_exceeded: {
    label: "Output limit exceeded",
    description:
      "The reply hit the output length limit before it was complete.",
  },
  empty_output: {
    label: "Empty output",
    description: "The model returned no text.",
  },
  incomplete_output: {
    label: "Incomplete output",
    description: "The call ended before the model returned a complete reply.",
  },
} satisfies Record<
  PublicContractViolationTurn["violation_kind"],
  ContractViolationDetail
>;
