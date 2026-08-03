import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import type { IndexHtmlTransformResult, Plugin } from "vite";

const HOME_MARKER = "<!-- deep20-static-home -->";
const STRUCTURED_DATA_MARKER = "<!-- deep20-structured-data -->";
const PUBLICATION_ORIGIN = "https://mindalyze-com.github.io";

interface StaticSiteMetadata {
  title: string;
  description: string;
  creatorName: string;
}

interface StaticCohort {
  subjectCount: number;
  iterations: number;
  maxQuestions: number;
}

interface StaticWinner {
  displayNames: string[];
  questionScore: string;
  joint: boolean;
}

interface StaticManifest {
  site: StaticSiteMetadata;
  cohort: StaticCohort;
  failurePenaltyOffset: number;
  builtAt: string;
  winner: StaticWinner | null;
}

interface StaticLeaderboardRow {
  rank: number;
  displayName: string;
  reasoningEffort: string;
  questionScore: string;
  successRate: string;
  executionId: string;
}

interface StaticPublication {
  manifest: StaticManifest;
  leaderboard: StaticLeaderboardRow[];
}

type JsonObject = Record<string, unknown>;

const objectValue = (value: unknown, label: string): JsonObject => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value as JsonObject;
};

const stringValue = (value: unknown, label: string): string => {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`${label} must be a non-empty string.`);
  }
  return value;
};

const numberValue = (value: unknown, label: string): number => {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`${label} must be a finite number.`);
  }
  return value;
};

const stringArray = (value: unknown, label: string): string[] => {
  if (!Array.isArray(value)) throw new Error(`${label} must be an array.`);
  return value.map((item, index) => stringValue(item, `${label}[${index}]`));
};

const readJson = (path: string): unknown => {
  const content = readFileSync(path, "utf8");
  return JSON.parse(content) as unknown;
};

const parseManifest = (value: unknown): StaticManifest => {
  const document = objectValue(value, "manifest");
  if (document.document_type !== "manifest" || document.schema_version !== 1) {
    throw new Error("Static homepage requires manifest schema version 1.");
  }
  const site = objectValue(document.site, "manifest.site");
  const cohort = objectValue(document.active_cohort, "manifest.active_cohort");
  const scorePolicy = objectValue(document.score_policy, "manifest.score_policy");
  const provenance = objectValue(document.provenance, "manifest.provenance");
  const targetIds = stringArray(cohort.target_ids, "manifest.active_cohort.target_ids");

  let winner: StaticWinner | null = null;
  if (document.winner !== null) {
    const winnerValue = objectValue(document.winner, "manifest.winner");
    winner = {
      displayNames: stringArray(winnerValue.display_names, "manifest.winner.display_names"),
      questionScore: stringValue(
        winnerValue.question_score,
        "manifest.winner.question_score",
      ),
      joint: winnerValue.joint === true,
    };
  }

  return {
    site: {
      title: stringValue(site.title, "manifest.site.title"),
      description: stringValue(site.description, "manifest.site.description"),
      creatorName: stringValue(site.creator_name, "manifest.site.creator_name"),
    },
    cohort: {
      subjectCount: targetIds.length,
      iterations: numberValue(cohort.iterations, "manifest.active_cohort.iterations"),
      maxQuestions: numberValue(
        cohort.max_questions,
        "manifest.active_cohort.max_questions",
      ),
    },
    failurePenaltyOffset: numberValue(
      scorePolicy.failure_penalty_offset,
      "manifest.score_policy.failure_penalty_offset",
    ),
    builtAt: stringValue(provenance.built_at, "manifest.provenance.built_at"),
    winner,
  };
};

const parseLeaderboard = (value: unknown): StaticLeaderboardRow[] => {
  const document = objectValue(value, "leaderboard");
  if (document.document_type !== "leaderboard" || document.schema_version !== 2) {
    throw new Error("Static homepage requires leaderboard schema version 2.");
  }
  if (!Array.isArray(document.leaderboard)) {
    throw new Error("leaderboard.leaderboard must be an array.");
  }

  return document.leaderboard.flatMap((item, index) => {
    const row = objectValue(item, `leaderboard.leaderboard[${index}]`);
    if (row.status !== "evaluated") return [];
    const model = objectValue(row.model, `leaderboard.leaderboard[${index}].model`);
    return [
      {
        rank: numberValue(row.rank, `leaderboard.leaderboard[${index}].rank`),
        displayName: stringValue(
          model.display_name,
          `leaderboard.leaderboard[${index}].model.display_name`,
        ),
        reasoningEffort: stringValue(
          model.reasoning_effort,
          `leaderboard.leaderboard[${index}].model.reasoning_effort`,
        ),
        questionScore: stringValue(
          row.question_score,
          `leaderboard.leaderboard[${index}].question_score`,
        ),
        successRate: stringValue(
          row.success_rate,
          `leaderboard.leaderboard[${index}].success_rate`,
        ),
        executionId: stringValue(
          row.execution_id,
          `leaderboard.leaderboard[${index}].execution_id`,
        ),
      },
    ];
  });
};

const loadPublication = (publicDirectory: string): StaticPublication => {
  const dataDirectory = resolve(publicDirectory, "data");
  return {
    manifest: parseManifest(readJson(resolve(dataDirectory, "manifest.json"))),
    leaderboard: parseLeaderboard(readJson(resolve(dataDirectory, "leaderboard.json"))),
  };
};

const escapeHtml = (value: string): string =>
  value.replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[character] ?? character,
  );

const escapeJson = (value: object): string =>
  JSON.stringify(value).replace(/</g, "\\u003c").replace(/>/g, "\\u003e");

const pathUrl = (base: string, path = ""): string =>
  escapeHtml(`${base}${path}`);

const formatDecimal = (value: string, places = 2): string => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) throw new Error(`Cannot format decimal value ${value}.`);
  return parsed.toFixed(places).replace(/\.0+$/, "").replace(/(\.\d*?)0+$/, "$1");
};

const formatPercent = (value: string): string => {
  const percentage = Number(value) * 100;
  if (!Number.isFinite(percentage)) throw new Error(`Cannot format percentage ${value}.`);
  return `${percentage.toFixed(1).replace(/\.0$/, "")}%`;
};

const formatDate = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) throw new Error(`Cannot format date ${value}.`);
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  return `${months[date.getUTCMonth()]} ${date.getUTCDate()}, ${date.getUTCFullYear()}`;
};

const renderResultRows = (rows: StaticLeaderboardRow[], base: string): string =>
  rows
    .slice(0, 3)
    .map(
      (row) => `
              <li>
                <span class="static-rank">${row.rank}</span>
                <div>
                  <a href="${pathUrl(base, `runs/${encodeURIComponent(row.executionId)}/`)}">
                    ${escapeHtml(row.displayName)}
                  </a>
                  <small>${escapeHtml(row.reasoningEffort)} reasoning · ${formatPercent(row.successRate)} success</small>
                </div>
                <strong>${formatDecimal(row.questionScore)}</strong>
              </li>`,
    )
    .join("");

const renderResults = (publication: StaticPublication, base: string): string => {
  const { manifest, leaderboard } = publication;
  const winner = manifest.winner;
  if (winner === null || leaderboard.length === 0) {
    return `
          <article class="static-result-card static-result-card--pending">
            <p class="static-eyebrow">Official comparison</p>
            <h3>Results are in progress.</h3>
            <p>Scores appear after a complete, integrity-checked run covers every subject.</p>
          </article>`;
  }
  const lowest = leaderboard[0];
  const highest = leaderboard[leaderboard.length - 1];
  if (lowest === undefined || highest === undefined) {
    throw new Error("Evaluated leaderboard is unexpectedly empty.");
  }
  const winnerLabel = winner.joint ? "Joint official leaders" : "Official leader";
  const scoreRange = `${formatDecimal(lowest.questionScore)}–${formatDecimal(highest.questionScore)}`;
  const modelCount = leaderboard.length;

  return `
          <div class="static-result-card">
            <div class="static-winner-copy">
              <p class="static-eyebrow">${winnerLabel}</p>
              <h3>${escapeHtml(winner.displayNames.join(" · "))}</h3>
              <p>
                The current leader averages <strong>${formatDecimal(winner.questionScore)}</strong>
                questions. The ${modelCount}-model cohort spans ${scoreRange}. Lower is better.
              </p>
            </div>
            <div class="static-score" aria-label="Question score ${formatDecimal(winner.questionScore)}">
              <strong>${formatDecimal(winner.questionScore)}</strong>
              <span>question score</span>
            </div>
          </div>
          <ol class="static-leaders" aria-label="Top three official results">
            ${renderResultRows(leaderboard, base)}
          </ol>`;
};

const renderHome = (publication: StaticPublication, base: string): string => {
  const { manifest, leaderboard } = publication;
  const { cohort, site } = manifest;
  const trialsPerModel = cohort.subjectCount * cohort.iterations;
  const totalTrials = trialsPerModel * leaderboard.length;
  const failurePenalty = cohort.maxQuestions + manifest.failurePenaltyOffset;

  return `
      <main class="static-home" id="static-home">
        <header class="static-header">
          <a class="static-brand" href="${pathUrl(base)}" aria-label="Deep20Bench overview">
            <span>D20B</span>
            <strong>${escapeHtml(site.title)}</strong>
          </a>
          <nav aria-label="Publication navigation">
            <a href="${pathUrl(base, "results/")}">Results</a>
            <a href="${pathUrl(base, "methodology/")}">Method</a>
            <a href="${pathUrl(base, "data/")}">Data</a>
          </nav>
        </header>

        <section class="static-hero">
          <div class="static-hero-copy">
            <p class="static-eyebrow">Independent benchmark · Twenty Questions for LLMs</p>
            <h1>Can an LLM ask its way to the answer?</h1>
            <p class="static-lead">
              A model identifies a hidden person, place, or thing by asking yes-or-no
              questions. Deep20Bench measures knowledge, question strategy, state tracking,
              and decision discipline.
            </p>
            <div class="static-actions">
              <a class="static-button static-button--primary" href="${pathUrl(base, "results/")}">
                See the benchmark <span aria-hidden="true">→</span>
              </a>
              <a class="static-button static-button--quiet" href="#executive-summary">
                Read the summary
              </a>
            </div>
          </div>
          <dl class="static-facts" aria-label="Benchmark size">
            <div><dt>Models tested</dt><dd>${leaderboard.length}</dd></div>
            <div><dt>Subjects</dt><dd>${cohort.subjectCount}</dd></div>
            <div><dt>Trials per model</dt><dd>${trialsPerModel}</dd></div>
            <div><dt>Official trials</dt><dd>${totalTrials}</dd></div>
          </dl>
        </section>

        <section class="static-section static-summary" id="executive-summary">
          <div class="static-section-heading">
            <p class="static-eyebrow">Executive summary</p>
            <h2>A focused test of adaptive reasoning.</h2>
            <p>
              Deep20Bench tests whether a model can turn broad knowledge into a useful sequence
              of questions, retain the answers, and commit to an exact guess.
            </p>
          </div>
          <div class="static-summary-grid">
            <article>
              <span>01</span>
              <h3>What it measures</h3>
              <p>Question quality, use of prior answers, and success before the turn limit.</p>
            </article>
            <article>
              <span>02</span>
              <h3>Why it matters</h3>
              <p>Useful systems must often clarify uncertainty before they can act well.</p>
            </article>
            <article>
              <span>03</span>
              <h3>What it does not claim</h3>
              <p>This is a narrow task benchmark, not a general ranking of model intelligence.</p>
            </article>
          </div>
        </section>

        <section class="static-section static-results">
          <div class="static-section-heading static-section-heading--split">
            <div>
              <p class="static-eyebrow">Current official results</p>
              <h2>Which models ask best?</h2>
            </div>
            <p>Published ${formatDate(manifest.builtAt)}. Every model completes ${trialsPerModel} trials.</p>
          </div>
          ${renderResults(publication, base)}
          <a class="static-text-link" href="${pathUrl(base, "results/")}">Explore all results and runs →</a>
        </section>

        <section class="static-section static-method">
          <div class="static-section-heading">
            <p class="static-eyebrow">How the benchmark works</p>
            <h2>Simple rules. Controlled answers.</h2>
          </div>
          <div class="static-method-grid">
            <article>
              <strong>1</strong>
              <div>
                <h3>Ask</h3>
                <p>The Guesser asks up to ${cohort.maxQuestions} counted yes-or-no questions.</p>
              </div>
            </article>
            <article>
              <strong>2</strong>
              <div>
                <h3>Check</h3>
                <p>An Oracle researches each question. A Reviewer checks every YES or NO. A blind Judge resolves disagreement.</p>
              </div>
            </article>
            <article>
              <strong>3</strong>
              <div>
                <h3>Score</h3>
                <p>Lower is better. A failed trial contributes ${failurePenalty} questions. Subjects carry equal weight.</p>
              </div>
            </article>
          </div>
          <div class="static-boundary">
            <p class="static-eyebrow">Core control</p>
            <h3>The model under test sees only the game.</h3>
            <p>
              It receives the category, its prior actions, and final YES, NO, or UNKNOWN tokens.
              It never sees private adjudicator prompts, evidence, searches, or hidden subject data.
            </p>
            <a class="static-text-link" href="${pathUrl(base, "methodology/")}">Read the full methodology →</a>
          </div>
        </section>

        <section class="static-section static-data">
          <div>
            <p class="static-eyebrow">Open evidence</p>
            <h2>Inspect the result behind the score.</h2>
          </div>
          <div>
            <p>
              The publication links scores to model runs, subjects, episode transcripts,
              answer evidence, contract violations, usage, cost, and timing.
            </p>
            <div class="static-actions">
              <a class="static-button static-button--primary" href="${pathUrl(base, "data/leaderboard.csv")}">Download CSV</a>
              <a class="static-button static-button--quiet" href="${pathUrl(base, "data/deep20bench-v7.json")}">Download JSON</a>
            </div>
          </div>
        </section>

        <footer class="static-footer">
          <p><strong>${escapeHtml(site.title)}</strong> · Created by ${escapeHtml(site.creatorName)}</p>
          <nav aria-label="Publication resources">
            <a href="${pathUrl(base, "story/")}">Origin and prior work</a>
            <a href="${pathUrl(base, "data/")}">Data and citation</a>
            <a href="https://github.com/mindalyze-com/deep-20-bench">Source code</a>
          </nav>
        </footer>
      </main>`;
};

const renderStructuredData = (publication: StaticPublication, base: string): string => {
  const canonicalUrl = new URL(base, PUBLICATION_ORIGIN).href;
  const { manifest, leaderboard } = publication;
  const data = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: manifest.site.title,
    description: manifest.site.description,
    url: canonicalUrl,
    creator: {
      "@type": "Person",
      name: manifest.site.creatorName,
    },
    dateModified: manifest.builtAt,
    isAccessibleForFree: true,
    keywords: [
      "large language models",
      "LLM benchmark",
      "Twenty Questions",
      "question strategy",
      "state tracking",
    ],
    variableMeasured: [
      "question score",
      "success rate",
      "contract compliance",
      "cost",
      "runtime",
    ],
    measurementTechnique: `${manifest.cohort.subjectCount} subjects, ${manifest.cohort.iterations} repeated trials per subject, ${leaderboard.length} evaluated models`,
    distribution: [
      {
        "@type": "DataDownload",
        encodingFormat: "text/csv",
        contentUrl: new URL(`${base}data/leaderboard.csv`, PUBLICATION_ORIGIN).href,
      },
      {
        "@type": "DataDownload",
        encodingFormat: "application/json",
        contentUrl: new URL(`${base}data/deep20bench-v7.json`, PUBLICATION_ORIGIN).href,
      },
    ],
  };
  return `<script type="application/ld+json">${escapeJson(data)}</script>`;
};

const replaceMarker = (html: string, marker: string, content: string): string => {
  const first = html.indexOf(marker);
  if (first < 0 || html.indexOf(marker, first + marker.length) >= 0) {
    throw new Error(`Expected exactly one ${marker} marker in index.html.`);
  }
  return html.replace(marker, content);
};

const removeTrailingWhitespace = (html: string): string => html.replace(/[ \t]+$/gm, "");

export const staticHomepagePlugin = (publicDirectory: string, base: string): Plugin => ({
  name: "deep20-static-homepage",
  transformIndexHtml(html): IndexHtmlTransformResult {
    const publication = loadPublication(publicDirectory);
    const withHome = replaceMarker(html, HOME_MARKER, renderHome(publication, base));
    return removeTrailingWhitespace(
      replaceMarker(
        withHome,
        STRUCTURED_DATA_MARKER,
        renderStructuredData(publication, base),
      ),
    );
  },
});
