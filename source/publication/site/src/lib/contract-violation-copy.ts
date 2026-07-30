import type { PublicContractViolationTurn } from "./types";

export interface ContractViolationDetail {
  label: string;
  description: string;
}

export const contractViolationDetails = {
  invalid_json: {
    label: "Invalid JSON",
    description: "The response could not be decoded as one complete JSON action.",
  },
  invalid_action: {
    label: "Invalid action",
    description:
      "The response contained JSON, but it did not match either allowed ASK or GUESS action.",
  },
  output_limit_exceeded: {
    label: "Output limit exceeded",
    description:
      "The provider reached the configured output limit before returning a complete action.",
  },
  empty_output: {
    label: "Empty output",
    description: "The provider completed without returning any action text.",
  },
  incomplete_output: {
    label: "Incomplete output",
    description: "The provider call ended without returning a completed structured action.",
  },
} satisfies Record<
  PublicContractViolationTurn["violation_kind"],
  ContractViolationDetail
>;
