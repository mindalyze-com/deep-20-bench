import { shallowRef } from "vue";
import type {
  AppBuildDocument,
  EditionsDocument,
  EpisodeDocument,
  LeaderboardDocument,
  ManifestDocument,
  RepeatAveragesDocument,
  RunDocument,
  SubjectDocument,
} from "./types";

export const selectedEditionId = shallowRef("1.0");
export const pendingEditionId = shallowRef<string | null>(null);
export const editionsIndex = shallowRef<EditionsDocument | null>(null);
const editionPath = (file: string, editionId = selectedEditionId.value): string =>
  `editions/${encodeURIComponent(editionId)}/${file}`;

const cache = new Map<string, Promise<unknown>>();
const preloaded = new Map<string, unknown>();
const dataBase = `${import.meta.env.BASE_URL}data/`;

export type PublicationDocument =
  | EditionsDocument
  | ManifestDocument
  | AppBuildDocument
  | LeaderboardDocument
  | RepeatAveragesDocument
  | RunDocument
  | SubjectDocument
  | EpisodeDocument;

const documentPath = (document: PublicationDocument): string => {
  switch (document.document_type) {
    case "editions":
      return "editions.json";
    case "manifest":
      return editionPath("manifest.json", document.edition_id);
    case "app_build":
      return "app-build.json";
    case "leaderboard":
      return editionPath("leaderboard.json", document.edition_id);
    case "repeat_averages":
      return editionPath("repeat-averages.json", document.edition_id);
    case "run":
      return `runs/${encodeURIComponent(document.run.execution_id)}.json`;
    case "subject":
      return `runs/${encodeURIComponent(document.execution_id)}/subjects/${encodeURIComponent(document.target_id)}.json`;
    case "episode":
      return `runs/${encodeURIComponent(document.execution_id)}/subjects/${encodeURIComponent(document.target_id)}/episodes/${encodeURIComponent(document.trial_id)}.json`;
  }
};

const objectValue = (value: unknown): Record<string, unknown> | null =>
  typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;

export const parsePublicationDocument = (value: unknown): PublicationDocument => {
  const candidate = objectValue(value);
  if (candidate === null || typeof candidate.document_type !== "string") {
    throw new Error("Preloaded publication data contains an unsupported document.");
  }
  const expectedVersions: Readonly<Record<string, number>> = {
    editions: 1,
    manifest: 2,
    app_build: 1,
    leaderboard: 4,
    repeat_averages: 2,
    run: 4,
    subject: 2,
    episode: 3,
  };
  const expectedVersion = expectedVersions[candidate.document_type];
  if (expectedVersion === undefined || candidate.schema_version !== expectedVersion) {
    throw new Error("Preloaded publication data uses an unsupported schema version.");
  }
  if (candidate.document_type !== "app_build" && candidate.document_type !== "editions") {
    if (typeof candidate.edition_id !== "string" || !/^[0-9]+\.[0-9]+$/.test(candidate.edition_id)) {
      throw new Error("Publication document has no valid edition identity.");
    }
  }
  if (candidate.document_type === "editions") {
    if (typeof candidate.default_edition_id !== "string" || !Array.isArray(candidate.editions)) {
      throw new Error("Publication edition index is invalid.");
    }
    const ids = new Set<string>();
    const runs = new Set<string>();
    for (const raw of candidate.editions) {
      const edition = objectValue(raw);
      if (edition === null || typeof edition.edition_id !== "string" ||
          !/^[0-9]+\.[0-9]+$/.test(edition.edition_id) || ids.has(edition.edition_id) ||
          typeof edition.label !== "string" || !["current", "previous"].includes(String(edition.status)) ||
          !Array.isArray(edition.runs)) throw new Error("Publication edition index is invalid.");
      ids.add(edition.edition_id);
      for (const rawRun of edition.runs) {
        const run = objectValue(rawRun);
        if (run === null || typeof run.execution_id !== "string" || runs.has(run.execution_id) ||
            typeof run.model_id !== "string" || !Array.isArray(run.target_ids) ||
            run.target_ids.some(id => typeof id !== "string")) {
          throw new Error("Publication edition run ownership is invalid.");
        }
        runs.add(run.execution_id);
      }
    }
    if (!ids.has(candidate.default_edition_id)) throw new Error("Default edition is unavailable.");
  }
  if (candidate.document_type === "manifest") {
    const cohort = objectValue(candidate.active_cohort);
    if (cohort === null || cohort.edition_id !== candidate.edition_id ||
        candidate.dataset_schema_version !== 10 || !Array.isArray(candidate.official_runs)) {
      throw new Error("Publication manifest edition is inconsistent.");
    }
  }
  if (candidate.document_type === "run") {
    const run = objectValue(candidate.run);
    if (run === null || typeof run.execution_id !== "string") {
      throw new Error("Preloaded run data has no execution identity.");
    }
  }
  if (candidate.document_type === "subject" || candidate.document_type === "episode") {
    if (
      typeof candidate.execution_id !== "string" ||
      typeof candidate.target_id !== "string"
    ) {
      throw new Error("Preloaded evidence data has no route identity.");
    }
  }
  if (candidate.document_type === "episode" && typeof candidate.trial_id !== "string") {
    throw new Error("Preloaded episode data has no trial identity.");
  }
  if (candidate.document_type === "episode") {
    const episode = objectValue(candidate.episode);
    if (episode === null || !Array.isArray(episode.turns)) throw new Error("Episode transcript is invalid.");
    for (const raw of episode.turns) {
      const turn = objectValue(raw);
      if (turn === null) throw new Error("Episode transcript is invalid.");
      if (turn.turn_type !== "action") continue;
      const tokens = turn.action === "ASK"
        ? ["YES", "RATHER_YES", "RATHER_NO", "NO", "UNKNOWN"] : ["YES", "NO", "UNKNOWN"];
      if (!tokens.includes(String(turn.answer))) throw new Error("Episode answer is invalid.");
    }
  }
  return candidate as unknown as PublicationDocument;
};

const validateOwnership = (document: PublicationDocument): void => {
  const index = editionsIndex.value;
  if (index === null || document.document_type === "app_build" || document.document_type === "editions") return;
  const edition = index.editions.find(item => item.edition_id === document.edition_id);
  if (edition === undefined) throw new Error("Publication edition is unavailable.");
  if (document.document_type === "run" || document.document_type === "subject" || document.document_type === "episode") {
    const executionId = document.document_type === "run" ? document.run.execution_id : document.execution_id;
    const run = edition.runs.find(item => item.execution_id === executionId);
    if (run === undefined || (document.document_type !== "run" && !run.target_ids.includes(document.target_id))) {
      throw new Error("Publication evidence belongs to a different edition.");
    }
  }
  if (document.document_type === "episode" &&
      peekManifest(document.edition_id)?.active_cohort.eligibility.kind === "historical_standard" &&
      document.episode.turns.some(turn => turn.turn_type === "action" &&
        ["RATHER_YES", "RATHER_NO"].includes(turn.answer))) {
    throw new Error("Standard edition transcript contains a qualified answer.");
  }
};

export const resetPublicationData = (): void => {
  cache.clear();
  preloaded.clear();
  selectedEditionId.value = "1.0";
  pendingEditionId.value = null;
  editionsIndex.value = null;
};

export const seedPublicationData = (documents: readonly unknown[]): void => {
  const parsed = documents.map(parsePublicationDocument);
  const index = parsed.find(document => document.document_type === "editions");
  if (index !== undefined) editionsIndex.value = index;
  const paths = new Set<string>();
  for (const document of parsed) {
    const path = documentPath(document);
    if (document.document_type === "editions") editionsIndex.value = document;
    if (paths.has(path)) {
      throw new Error("Preloaded publication data contains a duplicate document.");
    }
    paths.add(path);
    preloaded.set(path, document);
    cache.set(`${dataBase}${path}`, Promise.resolve(document));
  }
  parsed.forEach(validateOwnership);
};

const peek = <Document>(path: string): Document | null =>
  (preloaded.get(path) as Document | undefined) ?? null;

export const peekManifest = (editionId = selectedEditionId.value): ManifestDocument | null =>
  peek<ManifestDocument>(editionPath("manifest.json", editionId));

export const peekLeaderboard = (editionId = selectedEditionId.value): LeaderboardDocument | null =>
  peek<LeaderboardDocument>(editionPath("leaderboard.json", editionId));

export const peekRepeatAverages = (editionId = selectedEditionId.value): RepeatAveragesDocument | null =>
  peek<RepeatAveragesDocument>(editionPath("repeat-averages.json", editionId));

export const peekRun = (executionId: string): RunDocument | null =>
  peek<RunDocument>(`runs/${encodeURIComponent(executionId)}.json`);

export const peekSubject = (
  executionId: string,
  targetId: string,
): SubjectDocument | null =>
  peek<SubjectDocument>(
    `runs/${encodeURIComponent(executionId)}/subjects/${encodeURIComponent(targetId)}.json`,
  );

export const peekOfficialRuns = (): RunDocument[] | null => {
  const manifest = peekManifest();
  if (manifest === null) return null;
  const documents = manifest.official_runs.map((reference) =>
    peekRun(reference.execution_id),
  );
  return documents.every((document) => document !== null)
    ? (documents as RunDocument[])
    : null;
};

const request = <Document extends PublicationDocument>(
  path: string,
  expectedType: Document extends { document_type: infer Type } ? Type : never,
): Promise<Document> => {
  const url = `${dataBase}${path}`;
  const existing = cache.get(url);
  if (existing !== undefined) return existing as Promise<Document>;
  const pending = fetch(url, { credentials: "same-origin" })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(
          response.status === 404
            ? "No publication data exists for this page."
            : "Publication data could not be loaded. Try again.",
        );
      }
      let value: unknown;
      try {
        value = await response.json();
      } catch {
        throw new Error("Publication data is unavailable for this page.");
      }
      if (
        typeof value !== "object" ||
        value === null ||
        !("document_type" in value) ||
        value.document_type !== expectedType
      ) {
        throw new Error("Publication data could not be read. Try again.");
      }
      const parsed = parsePublicationDocument(value);
      validateOwnership(parsed);
      if (documentPath(parsed) !== path) {
        throw new Error("Publication document does not match the requested edition or route.");
      }
      preloaded.set(path, parsed);
      return parsed as Document;
    })
    .catch((error: unknown) => {
      cache.delete(url);
      throw error;
    });
  cache.set(url, pending);
  return pending;
};

export const getEditions = async (): Promise<EditionsDocument> => {
  const document = await request<EditionsDocument>("editions.json", "editions");
  editionsIndex.value = document;
  return document;
};

export const getManifest = (editionId = selectedEditionId.value): Promise<ManifestDocument> =>
  request<ManifestDocument>(editionPath("manifest.json", editionId), "manifest");

export const getAppBuild = (): Promise<AppBuildDocument> =>
  request<AppBuildDocument>("app-build.json", "app_build");

export const getLeaderboard = (editionId = selectedEditionId.value): Promise<LeaderboardDocument> =>
  request<LeaderboardDocument>(editionPath("leaderboard.json", editionId), "leaderboard");

export const getRepeatAverages = (editionId = selectedEditionId.value): Promise<RepeatAveragesDocument> =>
  request<RepeatAveragesDocument>(editionPath("repeat-averages.json", editionId), "repeat_averages");

export const getRun = (executionId: string): Promise<RunDocument> =>
  request<RunDocument>(`runs/${encodeURIComponent(executionId)}.json`, "run").then(
    (document) => {
      if (document.run.execution_id !== executionId) {
        throw new Error("Publication data could not be read. Try again.");
      }
      return document;
    },
  );

export const getSubject = (
  executionId: string,
  targetId: string,
): Promise<SubjectDocument> =>
  request<SubjectDocument>(
    `runs/${encodeURIComponent(executionId)}/subjects/${encodeURIComponent(targetId)}.json`,
    "subject",
  ).then((document) => {
    if (document.execution_id !== executionId || document.target_id !== targetId) {
      throw new Error("Publication data could not be read. Try again.");
    }
    return document;
  });

export const getEpisode = (
  executionId: string,
  targetId: string,
  trialId: string,
): Promise<EpisodeDocument> =>
  request<EpisodeDocument>(
    `runs/${encodeURIComponent(executionId)}/subjects/${encodeURIComponent(targetId)}/episodes/${encodeURIComponent(trialId)}.json`,
    "episode",
  ).then((document) => {
    if (
      document.execution_id !== executionId ||
      document.target_id !== targetId ||
      document.trial_id !== trialId
    ) {
      throw new Error("Publication data could not be read. Try again.");
    }
    return document;
  });

export const getOfficialRuns = async (): Promise<RunDocument[]> => {
  const manifest = await getManifest();
  return Promise.all(
    manifest.official_runs.map((reference) => getRun(reference.execution_id)),
  );
};

export const publicDownloadUrl = (filename: string): string =>
  `${dataBase}${filename}`;

export const editionDownloadUrl = (filename: string, editionId = selectedEditionId.value): string =>
  publicDownloadUrl(editionPath(filename, editionId));
