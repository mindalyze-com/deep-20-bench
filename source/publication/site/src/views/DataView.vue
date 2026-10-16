<script setup lang="ts">
import { editionRoute } from "@/lib/route-location";
import { ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import PublicationTime from "@/components/PublicationTime.vue";
import { getManifest, peekManifest, publicDownloadUrl, editionDownloadUrl } from "@/lib/api";
import { usePageRouteContext } from "@/lib/route-context";
import {
  citationResource,
  dataLicenseResource,
  softwareLicenseDescription,
  softwareLicenseResource,
} from "@/lib/site-resources";
import type { ManifestDocument } from "@/lib/types";
import { usePublicationLoad } from "@/lib/use-publication-load";

const initialManifest = peekManifest();
const manifest = ref<ManifestDocument | null>(initialManifest);
usePageRouteContext({
  title: "Data",
  description:
    "Download the public Deep20Bench record, trace each result, and run independent analyses.",
});
const { loading, error } = usePublicationLoad(async () => {
  manifest.value = await getManifest();
}, "Publication data is unavailable.", initialManifest !== null);

const sizeLabel = (bytes: number): string =>
  bytes >= 1_000_000
    ? `${(bytes / 1_000_000).toFixed(1)} MB`
    : `${Math.max(1, Math.round(bytes / 1_000))} KB`;
const downloadSize = (path: string): string | null => {
  const download = manifest.value?.downloads?.find((item) => item.path === path);
  return download === undefined ? null : sizeLabel(download.size_bytes);
};
</script>

<template>
  <div id="route-content" class="page data-page" tabindex="-1">
    <LoadingState
      v-if="loading"
      label="Loading data details"
    />
    <ErrorState v-else-if="error !== null" :message="error" />
    <template v-else-if="manifest !== null">
      <section class="page-hero site-boundary-shell">
        <div class="page-hero-inner site-boundary">
          <div>
            <p class="eyebrow">Public data</p>
            <h1>Deep20Bench {{ manifest.active_cohort.edition_label }} dataset.</h1>
          </div>
          <div class="lede data-lede">
            <p>
              Deep20Bench publishes all the data behind its leaderboard, not only the averages:
              runs, rounds, transcripts, evidence, outcomes, cost, and timing. Project-authored
              data may be reused under <a :href="dataLicenseResource.href">CC BY 4.0</a> with
              attribution; third-party evidence excerpts are not covered.
            </p>
            <ul aria-label="What the public data supports">
              <li>Trace each published result.</li>
              <li>Reproduce the official summaries.</li>
              <li>Build your own evaluations.</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="content-section flow-stage" aria-labelledby="download-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow flow-step"><span>01</span> Choose a format</p>
              <h2 id="download-title">Pick the file you need.</h2>
            </div>
            <p>
              Start with the JSON file. It holds everything in the CSV file and more.
            </p>
          </header>

          <div class="card-grid download-grid">
            <article class="card download-card download-card--primary">
              <p class="file-type">JSON · schema v{{ manifest.dataset_schema_version }}</p>
              <h3>Full public dataset</h3>
              <p>Edition rules, models, runs, subjects, rounds, scores, and build details.</p>
              <a
                class="button button-primary"
                :href="editionDownloadUrl('deep20bench-v10.json')"
                download
              >
                Download JSON<template v-if="downloadSize('deep20bench-v10.json')">
                  ({{ downloadSize("deep20bench-v10.json") }})</template> ↓
              </a>
            </article>
            <article class="card download-card">
              <p class="file-type">CSV · UTF-8</p>
              <h3>Leaderboard table</h3>
              <p>
                One row per ranked model. Long decimals are rounded to 6 places; the JSON file
                keeps exact values.
              </p>
              <a
                class="button button-secondary"
                :href="editionDownloadUrl('leaderboard.csv')"
                download
              >
                Download CSV<template v-if="downloadSize('leaderboard.csv')">
                  ({{ downloadSize("leaderboard.csv") }})</template> ↓
              </a>
            </article>
            <article class="card download-card">
              <p class="file-type">JSON Schema · draft 2020-12</p>
              <h3>Public data schema</h3>
              <p>The structure, required fields, and allowed values of data format v10.</p>
              <a
                class="button button-secondary"
                :href="editionDownloadUrl('deep20bench-v10.schema.json')"
                download
              >
                Download schema<template v-if="downloadSize('deep20bench-v10.schema.json')">
                  ({{ downloadSize("deep20bench-v10.schema.json") }})</template> ↓
              </a>
            </article>
          </div>
        </div>
      </section>

      <section class="content-section" aria-label="Version 9 compatibility">
        <div class="content-inner">
          <h2>Older v9 download</h2>
          <p>The <a :href="publicDownloadUrl('deep20bench-v9.json')">v9 dataset</a> and
            <a :href="publicDownloadUrl('deep20bench-v9.schema.json')">v9 schema</a> are still
            updated for edition 1.0. Version 9 cannot hold Rather yes and Rather no answers, so
            edition 1.1 results are only in the v10 files above.</p>
        </div>
      </section>
      <section class="content-section flow-stage" aria-labelledby="field-guide-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow flow-step"><span>02</span> Explore the file</p>
              <h2 id="field-guide-title">Find the main records.</h2>
            </div>
            <p>These four paths cover rankings, runs, rounds, and transcripts.</p>
          </header>

          <div class="field-guide">
            <dl class="field-paths">
              <div>
                <dt><code>leaderboard[]</code></dt>
                <dd>Ranks, models, question scores, solved rounds, format errors, cost, and time.</dd>
              </div>
              <div>
                <dt><code>official_runs[]</code></dt>
                <dd>Each ranked run in full: settings, totals, subjects, and all models used.</dd>
              </div>
              <div>
                <dt><code>subjects[].trials[]</code></dt>
                <dd>Each round's outcome, counted questions, score, cost, duration, and format errors.</dd>
              </div>
              <div>
                <dt><code>trials[].episode</code></dt>
                <dd>The round transcript: questions, answers, evidence, usage, timing, and format errors.</dd>
              </div>
            </dl>
            <div class="query-example">
              <div>
                <p class="eyebrow">Example query</p>
                <p>Print each model's rank, name, and exact question score.</p>
              </div>
              <pre><code>jq -r '.leaderboard[] | [.rank, .model.display_name, .question_score] | @tsv' deep20bench-v10.json</code></pre>
            </div>
          </div>

          <p class="eyebrow csv-notes-title">CSV column notes</p>
          <dl class="csv-notes" aria-label="CSV column notes">
            <div>
              <dt><code>ideal_distance_rank</code></dt>
              <dd>The rank shown on the Efficiency page.</dd>
            </div>
            <div>
              <dt><code>efficiency_rank</code></dt>
              <dd>
                An older cost-adjusted rank, the same as <code>product_efficiency_rank</code>.
                Kept for existing users of the file.
              </dd>
            </div>
            <div>
              <dt><code>contract_status</code></dt>
              <dd>
                Reply format: <code>clean</code> (no format errors), <code>breached</code> (at
                least one format error), or <code>not_evaluable</code> (not checked).
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section class="content-section flow-stage" aria-labelledby="release-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow flow-step"><span>03</span> Verify and reuse</p>
              <h2 id="release-title">Check the release details.</h2>
            </div>
            <p>See what went into this build, then cite and reuse it.</p>
          </header>

          <dl class="stats-grid release-facts" aria-label="Build details">
            <div>
              <dt>Run files checked</dt>
              <dd>
                {{ manifest.provenance.source_run_count }}
                <small>All editions, including replaced and unranked runs.</small>
              </dd>
            </div>
            <div>
              <dt>Ranked runs</dt>
              <dd>
                {{ manifest.provenance.official_run_count }}
                <small>The newest complete run of each model in this edition.</small>
              </dd>
            </div>
            <div>
              <dt>Game engine version</dt>
              <dd>
                v{{ manifest.active_cohort.benchmark_version }}
                <small>Not the data format version.</small>
              </dd>
            </div>
            <div>
              <dt>Latest completion</dt>
              <dd>
                <PublicationTime
                  v-if="manifest.provenance.latest_completed_at !== null"
                  :value="manifest.provenance.latest_completed_at"
                  date-only
                />
                <template v-else>-</template>
              </dd>
            </div>
            <div>
              <dt>Edition rules ID</dt>
              <dd>
                <code>{{ manifest.active_cohort.cohort_id }}</code>
                <small>Names the accepted settings of this edition in the data.</small>
              </dd>
            </div>
            <div class="release-checksum">
              <dt>Subject catalog SHA-256</dt>
              <dd><code>{{ manifest.provenance.subject_catalog_hash }}</code></dd>
            </div>
          </dl>

          <section id="published-contents" class="data-contract" aria-labelledby="contract-title">
            <div class="contract-intro">
              <p class="eyebrow">Contents</p>
              <h3 id="contract-title">What is and is not published.</h3>
            </div>
            <div class="contract-body">
              <div class="contract-columns">
                <article>
                  <h4>Included</h4>
                  <p>
                    IDs, model settings, scores, outcomes, costs, timestamps, the source code
                    commit, format errors, transcripts, Oracle evidence, and the source of each
                    reused answer. Format error records can include the Guesser's invalid
                    reply text.
                  </p>
                </article>
                <article>
                  <h4>Excluded</h4>
                  <p>
                    The answer-checking models' instructions, raw responses, and internal
                    decisions; hidden reasoning; full provider messages; credentials; and private
                    subject data. Private diagnostic files are not published.
                  </p>
                </article>
              </div>
              <p class="publisher-note">
                The site is built from finished, signed run files. Building it makes no model
                calls and does not change the run files.
              </p>
            </div>
          </section>

          <div class="card-grid reuse-panel">
            <article class="card">
              <p class="eyebrow">Citation</p>
              <h3>{{ manifest.site.citation_label }}</h3>
              <p>Deep20Bench, edition {{ manifest.active_cohort.edition_label }}.
                Published <PublicationTime :value="manifest.provenance.built_at" />.</p>
              <RouterLink :to="editionRoute('home')">Stable edition URL</RouterLink>
              <a :href="citationResource.href" target="_blank" rel="noreferrer">
                {{ citationResource.label }} ↗
              </a>
            </article>
            <article class="card">
              <p class="eyebrow">Data license</p>
              <h3>CC BY 4.0</h3>
              <p>Project-authored result data may be reused with attribution. Third-party evidence excerpts are excluded.</p>
              <a :href="dataLicenseResource.href" target="_blank" rel="noreferrer">
                {{ dataLicenseResource.label }} ↗
              </a>
            </article>
            <article class="card">
              <p class="eyebrow">Software license</p>
              <h3>Source available</h3>
              <p>{{ softwareLicenseDescription }}</p>
              <a :href="softwareLicenseResource.href" target="_blank" rel="noreferrer">
                {{ softwareLicenseResource.label }} ↗
              </a>
            </article>
          </div>
        </div>
      </section>

      <section class="content-section">
        <nav class="content-inner data-next" aria-label="Continue from public data">
          <div>
            <p class="eyebrow">Continue</p>
            <h2>Inspect the results or read the method.</h2>
          </div>
          <div class="button-row">
            <RouterLink class="button button-primary" :to="editionRoute('results')">
              View official results →
            </RouterLink>
            <RouterLink
              class="button button-secondary"
              :to="editionRoute('methodology')"
            >
              How it works →
            </RouterLink>
          </div>
        </nav>
      </section>
    </template>
  </div>
</template>

<style scoped>
.data-lede p {
  margin: 0;
}

.data-lede ul {
  display: grid;
  gap: 0.45rem;
  margin: 1.1rem 0 0;
  padding: 1rem 0 0 1.1rem;
  border-top: 1px solid rgb(255 255 255 / 20%);
  color: var(--text-inverse);
  font-size: var(--text-small);
  font-weight: var(--font-weight-semibold);
}

.flow-step {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  letter-spacing: 0.1em;
}

.flow-step span {
  display: inline-grid;
  width: 1.9rem;
  height: 1.9rem;
  border: var(--rule-strong);
  border-radius: 50%;
  place-items: center;
  letter-spacing: 0;
}

.download-grid {
  grid-template-columns: minmax(0, 1.24fr) minmax(0, 1fr) minmax(0, 1fr);
}

.download-card {
  display: flex;
  min-height: 16rem;
  gap: 0.85rem;
  flex-direction: column;
  align-items: flex-start;
}

.download-card h3 {
  margin: 0;
  font-size: var(--text-card-title);
  line-height: var(--text-card-title--line-height);
}

.download-card p:not(.file-type) {
  max-width: 32rem;
  line-height: 1.6;
}

.download-card .button {
  margin-top: auto;
}

.download-card--primary {
  background: var(--blue);
  color: var(--text-inverse);
}

.download-card--primary p:not(.file-type) {
  color: var(--text-inverse);
}

.file-type {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-extrabold);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.download-card--primary .file-type {
  color: var(--text-inverse);
}

.field-guide {
  display: grid;
  gap: 1px;
  border: var(--rule-default);
  background: var(--border-default);
}

.field-paths {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin: 0;
  background: var(--border-default);
}

.field-paths > div {
  min-width: 0;
  padding: 1.25rem;
  background: var(--surface-raised);
}

.field-paths dt {
  margin: 0;
  font-size: var(--text-small);
  font-weight: var(--font-weight-bold);
}

.field-paths dd {
  margin: 0.6rem 0 0;
  color: var(--text-secondary);
  font-size: var(--text-small);
  line-height: 1.55;
}

.query-example {
  display: grid;
  grid-template-columns: minmax(12rem, 0.28fr) minmax(0, 1fr);
  gap: clamp(1.2rem, 3vw, 2.5rem);
  align-items: center;
  padding: 1.25rem;
  background: var(--surface-inverse);
  color: var(--text-inverse);
}

.query-example p {
  margin: 0;
}

.query-example p:not(.eyebrow) {
  color: var(--text-inverse-muted);
  font-size: var(--text-small);
  line-height: 1.55;
}

.query-example pre {
  min-width: 0;
  margin: 0;
  padding: 0.95rem 1.1rem;
  overflow-x: auto;
  background: rgb(255 255 255 / 8%);
  color: var(--acid);
  font-size: var(--text-caption);
  line-height: 1.6;
}

.release-facts {
  grid-template-columns: repeat(5, minmax(0, 1fr));
  margin-bottom: 1rem;
}

.release-facts dd small {
  display: block;
  margin-top: 0.35rem;
  color: var(--muted);
  font-family: var(--font-body);
  font-size: var(--text-caption);
  line-height: 1.4;
}

.release-facts dd code {
  font-size: var(--text-small);
  overflow-wrap: anywhere;
}

.release-checksum {
  grid-column: 1 / -1;
}

.csv-notes-title {
  margin: 2rem 0 0;
}

.csv-notes {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin: 0.75rem 0 0;
}

.csv-notes dd {
  margin: 0.35rem 0 0;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.5;
}

@media (max-width: 760px) {
  .csv-notes {
    grid-template-columns: 1fr;
  }
}

.release-checksum dd {
  margin-top: 0.55rem;
  overflow-wrap: anywhere;
  font-family: var(--font-mono);
  font-size: var(--text-small);
  line-height: 1.5;
}

.data-contract {
  display: grid;
  grid-template-columns: minmax(0, 0.32fr) minmax(0, 1fr);
  gap: clamp(1.5rem, 4vw, 4rem);
  align-items: start;
  margin-bottom: 1rem;
  padding: clamp(1.5rem, 3vw, 2.5rem);
  background: var(--acid);
}

.data-contract h3 {
  max-width: 13ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-card-title);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.035em;
  line-height: var(--text-card-title--line-height);
}

.contract-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  border: var(--rule-strong);
  background: var(--ink);
}

.contract-columns article {
  min-width: 0;
  padding: 1.3rem;
  background: var(--surface-raised);
}

.contract-columns h4 {
  margin: 0 0 0.7rem;
  font-family: var(--font-display);
  font-size: 1.6rem;
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.02em;
  line-height: 1;
}

.contract-columns p {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-small);
  line-height: 1.6;
}

.publisher-note {
  margin: 1.5rem 0 0;
  font-size: var(--text-small);
  line-height: 1.6;
}

.reuse-panel {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.reuse-panel .card {
  display: flex;
  gap: 0.4rem;
  flex-direction: column;
  align-items: flex-start;
}

.reuse-panel .eyebrow {
  margin: 0;
}

.reuse-panel h3 {
  margin: 0.3rem 0 0;
  font-size: var(--text-card-title);
  line-height: var(--text-card-title--line-height);
}

.reuse-panel a {
  margin-top: 1.1rem;
  font-size: var(--text-small);
  font-weight: var(--font-weight-semibold);
}

.data-next {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  align-items: start;
}

.data-next h2 {
  max-width: 18ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2rem, 3.3vw, 3.2rem);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.043em;
  line-height: 0.98;
}

.data-next .button-row {
  justify-content: flex-end;
  margin: 0;
}

@media (max-width: 1200px) {
  .release-facts {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .download-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .download-card--primary {
    min-height: 0;
    grid-column: 1 / -1;
  }

  .field-paths {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .data-contract {
    grid-template-columns: 1fr;
  }

  .query-example {
    grid-template-columns: 1fr;
    align-items: start;
  }
}

@media (max-width: 760px) {
  .download-grid,
  .field-paths,
  .contract-columns,
  .reuse-panel {
    grid-template-columns: 1fr;
  }

  .release-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .download-card {
    min-height: 0;
  }

  .download-grid .button {
    width: 100%;
  }

  .data-next {
    display: grid;
    align-items: start;
  }

  .data-next .button-row,
  .data-next .button {
    width: 100%;
  }
}

@media (max-width: 520px) {
  .release-facts {
    grid-template-columns: 1fr;
  }
}
</style>
