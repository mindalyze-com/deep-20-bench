import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, type Locator, type Page } from "@playwright/test";

interface ManifestRun {
  execution_id: string;
}

interface PublicationManifest {
  official_runs: ManifestRun[];
}

interface RunSubject {
  target_id: string;
}

interface RunDocumentFixture {
  subjects: RunSubject[];
}

interface TrialFixture {
  trial_id: string;
  status: string;
}

interface SubjectDocumentFixture {
  trials: TrialFixture[];
}

export const docsRoot = path.resolve(process.cwd(), "../../../docs");
const fixtureDataRoot = path.resolve(
  process.cwd(),
  "tests/fixtures/publication/data",
);

export const derivePublicationPaths = (dataRoot: string) => {
  const manifest = JSON.parse(
    readFileSync(path.join(dataRoot, "manifest.json"), "utf8"),
  ) as PublicationManifest;
  const executionId = manifest.official_runs[0]?.execution_id;
  if (executionId === undefined) {
    throw new Error("The publication data has no official run.");
  }

  const runDocument = JSON.parse(
    readFileSync(path.join(dataRoot, "runs", `${executionId}.json`), "utf8"),
  ) as RunDocumentFixture;
  const targetId = runDocument.subjects[0]?.target_id;
  if (targetId === undefined) {
    throw new Error(`Run ${executionId} has no subjects.`);
  }

  const subjectDocument = JSON.parse(
    readFileSync(
      path.join(dataRoot, "runs", executionId, "subjects", `${targetId}.json`),
      "utf8",
    ),
  ) as SubjectDocumentFixture;
  const trialId = subjectDocument.trials.find(
    (trial) => trial.status !== "infrastructure_failure",
  )?.trial_id;
  if (trialId === undefined) {
    throw new Error(`Subject ${targetId} has no public episode.`);
  }

  const runPath = `runs/${executionId}/`;
  const subjectPath = `${runPath}subjects/${targetId}/`;
  return {
    episodePath: `${subjectPath}episodes/${trialId}/`,
    executionId,
    runDocument,
    runPath,
    subjectPath,
    targetId,
    trialId,
  };
};

const fixturePaths = derivePublicationPaths(fixtureDataRoot);
export const {
  episodePath,
  executionId,
  runDocument,
  runPath,
  subjectPath,
  targetId,
  trialId,
} = fixturePaths;
export const contractExampleRunPath = "runs/BX-20260728-official-M0006-010/";
export const contractExampleSubjectPath = `${contractExampleRunPath}subjects/T-0001/`;
export const contractExampleEpisodePath = `${contractExampleSubjectPath}episodes/trial-001/`;
export const contractExampleHref =
  "/deep-20-bench/runs/BX-20260728-official-M0006-010/subjects/T-0001/episodes/trial-001/?violation=first";
export const unknownExampleEpisodePath =
  "runs/BX-20260728-official-M0001-010/subjects/T-0002/episodes/trial-002/";

const traversalSubjectIndex = 1;
export const traversalSubjectId = runDocument.subjects[traversalSubjectIndex]?.target_id;
export const previousTraversalSubjectId =
  runDocument.subjects[traversalSubjectIndex - 1]?.target_id;
export const nextTraversalSubjectId =
  runDocument.subjects[traversalSubjectIndex + 1]?.target_id;

if (
  traversalSubjectId === undefined ||
  previousTraversalSubjectId === undefined ||
  nextTraversalSubjectId === undefined
) {
  throw new Error(`Run ${executionId} needs three subjects for traversal tests.`);
}

const traversalSubjectDocument = JSON.parse(
  readFileSync(
    path.join(
      fixtureDataRoot,
      "runs",
      executionId,
      "subjects",
      `${traversalSubjectId}.json`,
    ),
    "utf8",
  ),
) as SubjectDocumentFixture;
const traversalTrials = traversalSubjectDocument.trials.filter(
  (trial) => trial.status !== "infrastructure_failure",
);
export const firstTraversalTrialId = traversalTrials[0]?.trial_id;
export const lastTraversalTrialId = traversalTrials.at(-1)?.trial_id;

if (firstTraversalTrialId === undefined || lastTraversalTrialId === undefined) {
  throw new Error(`Subject ${traversalSubjectId} has no public episodes.`);
}

export const staticPaths = [
  "",
  "results/",
  "results/reliability/",
  "results/cost/",
  "results/time/",
  "results/efficiency/",
  "methodology/",
  "about/",
  "data/",
] as const;

export const waitForPublication = async (page: Page): Promise<void> => {
  await page.locator("#route-content").waitFor();
  const pathname = new URL(page.url()).pathname;
  const readySelector = pathname.includes("/episodes/")
    ? ".episode-tabs, .episode-view > .error-state"
    : pathname.includes("/subjects/")
      ? ".subject-overview-pane, .subject-workspace > .error-state"
      : pathname.includes("/runs/")
        ? ".run-overview-pane, .benchmark-workspace > .error-state"
        : pathname.includes("/results/")
          ? ".results-view > .content-section, .results-view > .error-state"
          : pathname.endsWith("/data/")
            ? ".data-page > .page-hero, .data-page > .error-state"
            : "#route-content";
  await page.locator(readySelector).first().waitFor({ state: "attached" });
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
};

export const expectNoViewportOverflow = async (page: Page): Promise<void> => {
  const overflow = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(overflow.scroll).toBeLessThanOrEqual(overflow.client + 1);
};

export const expectMinimumSize = async (
  locator: Locator,
  minimum: number,
): Promise<void> => {
  await expect(locator.first()).toBeVisible();
  const boxes = await locator.evaluateAll((elements) =>
    elements.map((element) => {
      const rectangle = element.getBoundingClientRect();
      return { width: rectangle.width, height: rectangle.height };
    }),
  );
  expect(boxes.length).toBeGreaterThan(0);
  for (const box of boxes) {
    expect(box.width).toBeGreaterThanOrEqual(minimum);
    expect(box.height).toBeGreaterThanOrEqual(minimum);
  }
};

export const expectVerticalGap = async (
  upper: Locator,
  lower: Locator,
  minimum: number,
): Promise<void> => {
  const upperBox = await upper.boundingBox();
  const lowerBox = await lower.boundingBox();
  expect(upperBox).not.toBeNull();
  expect(lowerBox).not.toBeNull();
  expect(lowerBox!.y - (upperBox!.y + upperBox!.height)).toBeGreaterThanOrEqual(
    minimum,
  );
};
