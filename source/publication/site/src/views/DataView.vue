<script setup lang="ts">
import { onActivated, onDeactivated, ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import { getManifest, publicDownloadUrl } from "@/lib/api";
import { date } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import { citationResource, dataLicenseResource } from "@/lib/site-resources";
import type { ManifestDocument } from "@/lib/types";

const manifest = ref<ManifestDocument | null>(null);
const error = ref<string | null>(null);
const active = ref(true);

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Data",
    description:
      "Download the public Deep20Bench record, trace each result, and run independent analyses.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

onActivated(() => {
  active.value = true;
  applyRouteContext();
});
onDeactivated(() => {
  active.value = false;
});

const load = async (): Promise<void> => {
  try {
    manifest.value = await getManifest();
    if (active.value) applyRouteContext();
  } catch (reason: unknown) {
    error.value = reason instanceof Error ? reason.message : "Publication data is unavailable.";
  }
};

void load();
applyRouteContext();
</script>

<template>
  <div id="route-content" class="page data-page" tabindex="-1">
    <LoadingState
      v-if="manifest === null && error === null"
      label="Loading data details"
    />
    <ErrorState v-else-if="error !== null" :message="error" />
    <template v-else-if="manifest !== null">
      <section class="page-hero site-boundary-shell">
        <div class="page-hero-inner site-boundary">
          <div>
            <p class="eyebrow">Public data</p>
            <h1>Download the public benchmark record.</h1>
          </div>
          <div class="lede data-lede">
            <p>
              Deep20Bench publishes the data behind its leaderboard, not only aggregate scores:
              runs, trials, transcripts, evidence, outcomes, cost, and timing.
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
              <h2 id="download-title">Start with the file that fits your task.</h2>
            </div>
            <p>
              JSON carries the complete public record, CSV carries the current rankings, and the
              schema validates both.
            </p>
          </header>

          <div class="card-grid download-grid">
            <article class="card download-card download-card--primary">
              <p class="file-type">JSON · schema v{{ manifest.dataset_schema_version }}</p>
              <h3>Full public dataset</h3>
              <p>Cohort rules, models, runs, subjects, episodes, scores, and build details.</p>
              <a
                class="button button-primary"
                :href="publicDownloadUrl('deep20bench-v9.json')"
                download
              >
                Download JSON ↓
              </a>
            </article>
            <article class="card download-card">
              <p class="file-type">CSV · UTF-8</p>
              <h3>Leaderboard table</h3>
              <p>One row per model with a selected complete run.</p>
              <a
                class="button button-secondary"
                :href="publicDownloadUrl('leaderboard.csv')"
                download
              >
                Download CSV ↓
              </a>
            </article>
            <article class="card download-card">
              <p class="file-type">JSON Schema · draft 2020-12</p>
              <h3>Public data schema</h3>
              <p>Types, required fields, enums, and nested public objects for schema v9.</p>
              <a
                class="button button-secondary"
                :href="publicDownloadUrl('deep20bench-v9.schema.json')"
                download
              >
                Download schema ↓
              </a>
            </article>
          </div>
        </div>
      </section>

      <section class="content-section flow-stage" aria-labelledby="field-guide-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow flow-step"><span>02</span> Explore the file</p>
              <h2 id="field-guide-title">Find the main records.</h2>
            </div>
            <p>These four paths cover rankings, runs, trials, and episode transcripts.</p>
          </header>

          <div class="field-guide">
            <dl class="field-paths">
              <div>
                <dt><code>leaderboard[]</code></dt>
                <dd>Ranks, model identity, question score, success, reliability, cost, and time.</dd>
              </div>
              <div>
                <dt><code>official_runs[]</code></dt>
                <dd>Full selected runs with configuration, totals, subjects, and component models.</dd>
              </div>
              <div>
                <dt><code>subjects[].trials[]</code></dt>
                <dd>Trial outcomes, counted questions, penalties, cost, duration, and contract status.</dd>
              </div>
              <div>
                <dt><code>trials[].episode</code></dt>
                <dd>Typed transcripts, public evidence, usage, timing, and visible format violations.</dd>
              </div>
            </dl>
            <div class="query-example">
              <div>
                <p class="eyebrow">Example query</p>
                <p>Print leaderboard rank, model name, and exact question score.</p>
              </div>
              <pre><code>jq -r '.leaderboard[] | [.rank, .model.display_name, .question_score] | @tsv' deep20bench-v9.json</code></pre>
            </div>
          </div>
        </div>
      </section>

      <section class="content-section flow-stage" aria-labelledby="release-title">
        <div class="content-inner">
          <header class="section-heading">
            <div>
              <p class="eyebrow flow-step"><span>03</span> Verify and reuse</p>
              <h2 id="release-title">Check the release details.</h2>
            </div>
            <p>Review what went into this build, then cite it and reuse it.</p>
          </header>

          <dl class="stats-grid release-facts" aria-label="Build details">
            <div>
              <dt>Validated source runs</dt>
              <dd>{{ manifest.provenance.source_run_count }}</dd>
            </div>
            <div>
              <dt>Selected official runs</dt>
              <dd>{{ manifest.provenance.official_run_count }}</dd>
            </div>
            <div>
              <dt>Benchmark protocol</dt>
              <dd>v{{ manifest.active_cohort.benchmark_version }}</dd>
            </div>
            <div>
              <dt>Latest completion</dt>
              <dd>{{ date(manifest.provenance.latest_completed_at) }}</dd>
            </div>
            <div>
              <dt>Active cohort</dt>
              <dd>{{ manifest.active_cohort.cohort_id }}</dd>
            </div>
            <div class="release-checksum">
              <dt>Subject catalog SHA-256</dt>
              <dd><code>{{ manifest.provenance.subject_catalog_hash }}</code></dd>
            </div>
          </dl>

          <section class="data-contract" aria-labelledby="contract-title">
            <div class="contract-intro">
              <p class="eyebrow">Contents</p>
              <h3 id="contract-title">Public and excluded.</h3>
            </div>
            <div class="contract-body">
              <div class="contract-columns">
                <article>
                  <h4>Included</h4>
                  <p>
                    IDs, model settings, scores, outcomes, costs, timestamps, source commit,
                    contract reliability, typed transcripts, and published Oracle evidence.
                  </p>
                </article>
                <article>
                  <h4>Excluded</h4>
                  <p>
                    Malformed completions, adjudicator prompts and decisions, hidden reasoning,
                    provider payloads, credentials, headers, sessions, and private subject state.
                  </p>
                </article>
              </div>
              <p class="publisher-note">
                The publisher reads completed signed run files. It makes no model calls and does
                not change source runs.
              </p>
            </div>
          </section>

          <div class="card-grid reuse-panel">
            <article class="card">
              <p class="eyebrow">Citation</p>
              <h3>{{ manifest.site.citation_label }}</h3>
              <p>Protocol v{{ manifest.active_cohort.benchmark_version }}</p>
              <a :href="citationResource.href" target="_blank" rel="noreferrer">
                {{ citationResource.label }} ↗
              </a>
            </article>
            <article class="card">
              <p class="eyebrow">Data licence</p>
              <h3>CC BY 4.0</h3>
              <p>Project-authored result data may be reused with attribution.</p>
              <a :href="dataLicenseResource.href" target="_blank" rel="noreferrer">
                {{ dataLicenseResource.label }} ↗
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
            <RouterLink class="button button-primary" :to="{ name: 'results' }">
              View official results →
            </RouterLink>
            <RouterLink
              class="button button-secondary"
              :to="{ name: 'methodology', hash: '#publication' }"
            >
              Read the publication method →
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

.release-checksum {
  grid-column: 1 / -1;
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
  align-items: end;
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
