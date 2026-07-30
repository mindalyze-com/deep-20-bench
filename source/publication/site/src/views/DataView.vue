<script setup lang="ts">
import { onActivated, onDeactivated, ref } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import { getManifest, publicDownloadUrl } from "@/lib/api";
import { date, isoDateTime } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { ManifestDocument } from "@/lib/types";

const manifest = ref<ManifestDocument | null>(null);
const error = ref<string | null>(null);
const active = ref(true);

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Data",
    description: "Download the Deep20Bench dataset and inspect its public contents.",
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
    <LoadingState v-if="manifest === null && error === null" label="Loading data details" />
    <ErrorState v-else-if="error !== null" :message="error" />
    <template v-else-if="manifest !== null">
      <section class="page-hero">
        <div class="page-hero-inner">
          <div>
            <p class="eyebrow">Public data</p>
            <h1>Download the data.</h1>
          </div>
          <p class="lede">
            JSON contains runs, subjects, episodes, transcripts, and telemetry. CSV contains the
            current leaderboard.
          </p>
        </div>
      </section>

      <section class="content-section">
        <div class="content-inner">
          <div class="download-grid">
            <article class="download-primary">
              <p class="file-type">JSON · schema v{{ manifest.dataset_schema_version }}</p>
              <h2>Full public dataset</h2>
              <p>Cohort rules, models, runs, subjects, episodes, scores, and build details.</p>
              <a
                class="button button-primary"
                :href="publicDownloadUrl('deep20bench-v6.json')"
                download
              >
                Download JSON ↓
              </a>
            </article>
            <article>
              <p class="file-type">CSV · UTF-8</p>
              <h2>Leaderboard table</h2>
              <p>One row per model with a selected complete run.</p>
              <a
                class="button button-secondary"
                :href="publicDownloadUrl('leaderboard.csv')"
                download
              >
                Download CSV ↓
              </a>
            </article>
          </div>

          <section class="provenance" aria-labelledby="provenance-title">
            <div>
              <p class="eyebrow">Build details</p>
              <h2 id="provenance-title">Included in this build.</h2>
            </div>
            <dl>
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
                <dt>Subject catalog SHA-256</dt>
                <dd><code>{{ manifest.provenance.subject_catalog_hash }}</code></dd>
              </div>
              <div>
                <dt>Active cohort</dt>
                <dd>{{ manifest.active_cohort.cohort_id }}</dd>
              </div>
            </dl>
          </section>

          <section class="data-contract" aria-labelledby="contract-title">
            <div>
              <p class="eyebrow">Contents</p>
              <h2 id="contract-title">Public and excluded.</h2>
            </div>
            <div class="contract-columns">
              <article>
                <h3>Included</h3>
                <p>
                  IDs, model settings, scores, outcomes, costs, timestamps, source commit,
                  contract reliability, typed transcripts, and published Oracle evidence.
                </p>
              </article>
              <article>
                <h3>Excluded</h3>
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
          </section>
        </div>
      </section>

      <footer class="data-build-note" aria-label="Publication build information">
        <p>
          Publication built ·
          <time :datetime="manifest.provenance.built_at">
            {{ isoDateTime(manifest.provenance.built_at) }}
          </time>
        </p>
      </footer>
    </template>
  </div>
</template>

<style scoped>
.download-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.download-grid article {
  display: flex;
  min-height: 23rem;
  padding: clamp(1.5rem, 4vw, 3rem);
  border: var(--rule-default);
  background: var(--paper-bright);
  flex-direction: column;
  align-items: flex-start;
}

.download-grid article.download-primary {
  background: var(--blue);
  color: white;
}

.file-type {
  margin: 0;
  font-size: var(--text-micro);
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.download-grid h2,
.provenance h2,
.data-contract h2 {
  max-width: 11ch;
  margin: auto 0 1rem;
  font-family: var(--font-display);
  font-size: clamp(2.3rem, 4vw, 4rem);
  font-weight: 470;
  letter-spacing: -0.043em;
  line-height: 0.98;
}

.download-grid article > p:not(.file-type) {
  max-width: 34rem;
  min-height: 4.5rem;
  color: var(--muted);
  line-height: 1.65;
}

.download-primary > p:not(.file-type) {
  color: white !important;
}

.download-grid .button {
  margin-top: 1rem;
}

.download-primary .button-primary {
  border-color: var(--acid);
  background: var(--acid);
}

.provenance,
.data-contract {
  display: grid;
  grid-template-columns: minmax(13rem, 0.45fr) minmax(0, 1fr);
  gap: clamp(2rem, 8vw, 8rem);
  margin-top: clamp(4rem, 9vw, 8rem);
  padding-top: 1rem;
  border-top: var(--rule-strong);
}

.provenance h2,
.data-contract h2 {
  margin: 0;
  font-size: clamp(2.5rem, 3.8vw, 3.8rem);
}

.provenance dl {
  margin: 0;
}

.provenance dl div {
  display: grid;
  grid-template-columns: minmax(9rem, 0.45fr) minmax(0, 1fr);
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: var(--rule-default);
}

.provenance dt {
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: 760;
  text-transform: uppercase;
}

.provenance dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.provenance code {
  font-size: var(--text-small);
}

.data-contract {
  padding: clamp(2rem, 5vw, 4rem);
  border-top: 0;
  background: var(--acid);
}

.contract-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  border: var(--rule-strong);
  background: var(--ink);
}

.contract-columns article {
  padding: 1.3rem;
  background: var(--paper-bright);
}

.contract-columns h3 {
  margin: 0 0 0.8rem;
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 500;
}

.contract-columns p,
.publisher-note {
  margin: 0;
  line-height: 1.7;
}

.publisher-note {
  grid-column: 2;
}

.data-build-note {
  display: flex;
  justify-content: flex-end;
  padding: 0 max(var(--gutter), calc((100vw - var(--max)) / 2)) 1.1rem;
}

.data-build-note p {
  margin: 0;
  color: rgb(12 17 27 / 34%);
  font-size: var(--text-micro);
  letter-spacing: 0.04em;
  line-height: 1.4;
  text-align: right;
}

.data-build-note time {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 760px) {
  .download-grid,
  .provenance,
  .data-contract,
  .contract-columns {
    grid-template-columns: 1fr;
  }

  .download-grid article {
    min-height: 23rem;
  }

  .publisher-note {
    grid-column: 1;
  }
}

@media (max-width: 500px) {
  .provenance dl div {
    grid-template-columns: 1fr;
  }
}
</style>
