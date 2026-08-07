export interface ModelNameParts {
  displayName: string;
  reasoningEffort: string | null;
}

const REASONING_EFFORT_SUFFIX =
  /^(.*)\s+\((none|minimal|low|medium|high|extra[-_ ]high|xhigh|max|maximum|default|non[-_ ]thinking)\)$/i;

export const splitModelName = (name: string): ModelNameParts => {
  const match = REASONING_EFFORT_SUFFIX.exec(name.trim());
  if (match === null) {
    return { displayName: name, reasoningEffort: null };
  }
  return {
    displayName: match[1]?.trim() || name,
    reasoningEffort: match[2]?.trim().toLowerCase().replaceAll("_", "-") ?? null,
  };
};
