<script setup lang="ts">
import { computed } from "vue";

import PublicationTime from "@/components/PublicationTime.vue";
import SubjectReferenceLink from "@/components/SubjectReferenceLink.vue";
import {
  integer,
  money,
  moneyEpisode,
  seconds,
  statusLabel,
} from "@/lib/format";
import type {
  PublicComponentTelemetry,
  PublicEpisodeDetail,
  PublicRunSummary,
  PublicTrialSummary,
} from "@/lib/types";

const props = defineProps<{
  run: PublicRunSummary;
  trial: PublicTrialSummary;
  episode: PublicEpisodeDetail;
}>();

interface TelemetryRow {
  role: string;
  values: PublicComponentTelemetry;
}

const evidenceCount = computed(() =>
  props.episode.turns.reduce(
    (total, turn) =>
      total + (turn.turn_type === "action" ? turn.evidence.length : 0),
    0,
  ),
);

const telemetryRows = computed<TelemetryRow[]>(() => [
  { role: "Guesser", values: props.episode.telemetry.guesser },
  { role: "Oracle support", values: props.episode.telemetry.oracle },
  { role: "Validator", values: props.episode.telemetry.validator },
]);
</script>

<template>
  <section
    id="technical"
    class="content-section episode-panel technical"
    role="tabpanel"
    aria-labelledby="episode-tab-usage technical-heading"
    tabindex="0"
  >
    <div class="content-inner">
      <header class="section-heading">
        <div>
          <p class="eyebrow">Technical details</p>
          <h2 id="technical-heading">Episode usage.</h2>
        </div>
        <p>
          Tokens, cache use, latency, and recorded cost for this episode. Model
          configuration is shown on the Run overview.
        </p>
      </header>

      <div class="technical-context">
        <article>
          <span>Hidden subject</span>
          <strong>{{ episode.subject_name }}</strong>
          <p>{{ episode.subject_description }}</p>
          <SubjectReferenceLink
            v-if="episode.subject_reference_url"
            :href="episode.subject_reference_url"
          />
        </article>
        <article>
          <span>Episode scope</span>
          <strong>
            {{ moneyEpisode(episode.total_cost_usd) }} across
            {{ episode.total_turns }} turns
          </strong>
          <p>
            Includes {{ evidenceCount }} evidence
            {{ evidenceCount === 1 ? "item" : "items" }} and all model activity for this
            episode.
          </p>
          <RouterLink
            :to="{ name: 'run', params: { executionId: run.execution_id } }"
          >
            Full run {{ money(run.total_cost_usd) }} <span aria-hidden="true">→</span>
          </RouterLink>
        </article>
        <article>
          <span>Public post-run view</span>
          <strong>Published actions and rejected Guesser text</strong>
          <p>
            Typed actions, canonical valid outputs, and rejected Guesser text are public.
            Adjudicator prompts, hidden reasoning, private identifiers, and provider
            payloads are excluded.
          </p>
        </article>
      </div>

      <div
        class="table-wrap telemetry-wrap"
        tabindex="0"
        aria-label="Scrollable component telemetry"
      >
        <table class="data-table telemetry-table">
          <caption class="visually-hidden">Component telemetry</caption>
          <thead>
            <tr>
              <th>Component</th>
              <th data-numeric>Calls</th>
              <th data-numeric>Total tokens</th>
              <th data-numeric>Input</th>
              <th data-numeric>Cached input</th>
              <th data-numeric>Cache write</th>
              <th data-numeric>Output</th>
              <th data-numeric>Reasoning</th>
              <th data-numeric>Latency</th>
              <th data-numeric>Cost</th>
              <th data-numeric>Cache savings</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in telemetryRows" :key="row.role">
              <th>{{ row.role }}</th>
              <td data-numeric>{{ row.values.calls }}</td>
              <td data-numeric>{{ integer(row.values.total_tokens) }}</td>
              <td data-numeric>{{ integer(row.values.input_tokens) }}</td>
              <td data-numeric>{{ integer(row.values.cached_input_tokens) }}</td>
              <td data-numeric>{{ integer(row.values.cache_write_tokens) }}</td>
              <td data-numeric>{{ integer(row.values.output_tokens) }}</td>
              <td data-numeric>{{ integer(row.values.reasoning_tokens) }}</td>
              <td data-numeric>{{ seconds(row.values.latency_ms) }} s</td>
              <td data-numeric>{{ moneyEpisode(row.values.cost_usd) }}</td>
              <td data-numeric>
                {{ moneyEpisode(row.values.estimated_cache_savings_usd) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <details class="disclosure provenance-details">
        <summary>
          <span>
            <strong>IDs and timing</strong>
            <small>Execution IDs, timestamps, and totals</small>
          </span>
          <span aria-hidden="true">View ↓</span>
        </summary>
        <dl>
          <div><dt>Execution</dt><dd><code>{{ run.execution_id }}</code></dd></div>
          <div><dt>Episode run</dt><dd><code>{{ episode.episode_run_id }}</code></dd></div>
          <div><dt>Episode</dt><dd><code>{{ episode.episode_id }}</code></dd></div>
          <div><dt>Trial</dt><dd><code>{{ trial.trial_id }}</code></dd></div>
          <div><dt>Started</dt><dd><PublicationTime :value="episode.started_at" /></dd></div>
          <div><dt>Completed</dt><dd><PublicationTime :value="episode.completed_at" /></dd></div>
          <div><dt>Git commit</dt><dd><code>{{ run.git_commit }}</code></dd></div>
          <div><dt>Cache status</dt><dd>{{ statusLabel(episode.cache_status) }}</dd></div>
          <div><dt>Total tokens</dt><dd>{{ integer(episode.total_tokens) }}</dd></div>
          <div><dt>Episode cost</dt><dd>{{ moneyEpisode(episode.total_cost_usd) }}</dd></div>
        </dl>
      </details>
    </div>
  </section>
</template>

<style scoped>
.technical {
  background: var(--surface-page);
}

.technical-context {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin-bottom: 1.2rem;
  border: var(--rule-default);
  background: var(--border-default);
}

.technical-context article {
  min-width: 0;
  padding: 1.2rem;
  background: var(--surface-raised);
}

.technical-context article > span,
.provenance-details dt {
  color: var(--text-secondary);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.technical-context strong {
  display: block;
  margin-top: 0.65rem;
  font-size: 0.92rem;
}

.technical-context p {
  color: var(--text-secondary);
  font-size: var(--text-micro);
  line-height: 1.6;
}

.technical-context a {
  color: var(--blue-ink);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
}

.telemetry-wrap {
  margin-top: 2rem;
}

.telemetry-table {
  min-width: 1120px;
}

.telemetry-table tbody th {
  font-size: var(--text-micro);
}

.provenance-details {
  margin-top: 2rem;
}

.provenance-details > dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
  border-top: var(--rule-default);
}

.provenance-details > dl > div {
  min-width: 0;
  padding: 1rem;
  border-right: var(--rule-default);
  border-bottom: var(--rule-default);
}

.provenance-details > dl > div:nth-child(even) {
  border-right: 0;
}

.provenance-details dd {
  margin: 0.4rem 0 0;
  font-size: var(--text-micro);
  overflow-wrap: anywhere;
}

@media (max-width: 780px) {
  .technical-context {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .provenance-details > dl {
    grid-template-columns: 1fr;
  }

  .provenance-details > dl > div,
  .provenance-details > dl > div:nth-child(even) {
    border-right: 0;
    border-bottom: var(--rule-default);
  }

  .provenance-details > dl > div:last-child {
    border-bottom: 0;
  }
}
</style>
