import type {
  AppBuildDocument,
  EpisodeDocument,
  LeaderboardDocument,
  ManifestDocument,
  RepeatAveragesDocument,
  RunDocument,
  SubjectDocument,
} from "./types";

const cache = new Map<string, Promise<unknown>>();
const preloaded = new Map<string, unknown>();
const dataBase = `${import.meta.env.BASE_URL}data/`;

export type PublicationDocument =
  | ManifestDocument
  | AppBuildDocument
  | LeaderboardDocument
  | RepeatAveragesDocument
  | RunDocument
  | SubjectDocument
  | EpisodeDocument;

const documentPath = (document: PublicationDocument): string => {
  switch (document.document_type) {
    case "manifest":
      return "manifest.json";
    case "app_build":
      return "app-build.json";
    case "leaderboard":
      return "leaderboard.json";
    case "repeat_averages":
      return "repeat-averages.json";
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
    manifest: 1,
    app_build: 1,
    leaderboard: 3,
    repeat_averages: 1,
    run: 3,
    subject: 1,
    episode: 2,
  };
  const expectedVersion = expectedVersions[candidate.document_type];
  if (expectedVersion === undefined || candidate.schema_version !== expectedVersion) {
    throw new Error("Preloaded publication data uses an unsupported schema version.");
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
  return candidate as unknown as PublicationDocument;
};

export const resetPublicationData = (): void => {
  cache.clear();
  preloaded.clear();
};

export const seedPublicationData = (documents: readonly unknown[]): void => {
  const paths = new Set<string>();
  for (const value of documents) {
    const document = parsePublicationDocument(value);
    const path = documentPath(document);
    if (paths.has(path)) {
      throw new Error("Preloaded publication data contains a duplicate document.");
    }
    paths.add(path);
    preloaded.set(path, document);
    cache.set(`${dataBase}${path}`, Promise.resolve(document));
  }
};

const peek = <Document>(path: string): Document | null =>
  (preloaded.get(path) as Document | undefined) ?? null;

export const peekManifest = (): ManifestDocument | null =>
  peek<ManifestDocument>("manifest.json");

export const peekLeaderboard = (): LeaderboardDocument | null =>
  peek<LeaderboardDocument>("leaderboard.json");

export const peekRepeatAverages = (): RepeatAveragesDocument | null =>
  peek<RepeatAveragesDocument>("repeat-averages.json");

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

const request = <Document>(
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
      return value as Document;
    })
    .catch((error: unknown) => {
      cache.delete(url);
      throw error;
    });
  cache.set(url, pending);
  return pending;
};

export const getManifest = (): Promise<ManifestDocument> =>
  request<ManifestDocument>("manifest.json", "manifest");

export const getAppBuild = (): Promise<AppBuildDocument> =>
  request<AppBuildDocument>("app-build.json", "app_build");

export const getLeaderboard = (): Promise<LeaderboardDocument> =>
  request<LeaderboardDocument>("leaderboard.json", "leaderboard");

export const getRepeatAverages = (): Promise<RepeatAveragesDocument> =>
  request<RepeatAveragesDocument>("repeat-averages.json", "repeat_averages");

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
