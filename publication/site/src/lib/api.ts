import type {
  EpisodeDocument,
  LeaderboardDocument,
  ManifestDocument,
  RunDocument,
  SubjectDocument,
} from "./types";

const cache = new Map<string, Promise<unknown>>();
const dataBase = `${import.meta.env.BASE_URL}data/`;

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
        throw new Error(`Publication data request failed (${response.status}).`);
      }
      const value: unknown = await response.json();
      if (
        typeof value !== "object" ||
        value === null ||
        !("document_type" in value) ||
        value.document_type !== expectedType
      ) {
        throw new Error("Publication data has an unexpected document type.");
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

export const getLeaderboard = (): Promise<LeaderboardDocument> =>
  request<LeaderboardDocument>("leaderboard.json", "leaderboard");

export const getRun = (executionId: string): Promise<RunDocument> =>
  request<RunDocument>(`runs/${encodeURIComponent(executionId)}.json`, "run").then(
    (document) => {
      if (document.run.execution_id !== executionId) {
        throw new Error("Run data does not match the requested execution.");
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
      throw new Error("Subject data does not match the requested route.");
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
      throw new Error("Episode data does not match the requested route.");
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
