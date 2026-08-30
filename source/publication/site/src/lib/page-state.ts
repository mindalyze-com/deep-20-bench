import {
  parsePublicationDocument,
  seedPublicationData,
  type PublicationDocument,
} from "./api";

export interface SerializedPageState {
  schema_version: 1;
  documents: PublicationDocument[];
}

const stateElementId = "deep20-page-state";

const parseState = (value: unknown): SerializedPageState => {
  if (
    typeof value !== "object" ||
    value === null ||
    !("schema_version" in value) ||
    value.schema_version !== 1 ||
    !("documents" in value) ||
    !Array.isArray(value.documents)
  ) {
    throw new Error("The embedded publication state is invalid.");
  }
  return {
    schema_version: 1,
    documents: value.documents.map(parsePublicationDocument),
  };
};

export const seedEmbeddedPageState = (): boolean => {
  const element = document.getElementById(stateElementId);
  if (element === null) return false;
  const state = parseState(JSON.parse(element.textContent ?? "null") as unknown);
  seedPublicationData(state.documents);
  return true;
};
