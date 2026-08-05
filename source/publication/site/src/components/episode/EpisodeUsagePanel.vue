<script setup lang="ts">
import { computed } from "vue";

import {
  dateTime,
  integer,
  money,
  moneyEpisode,
  reasoningEffortLabel,
  seconds,
  statusLabel,
} from "@/lib/format";
import type {
  PublicComponentTelemetry,
  PublicEpisodeDetail,
  PublicOracleSupportRole,
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

interface SupportRow {
  role: string;
  description: string;
  values: PublicOracleSupportRole;
}

interface ProviderRouteValues {
  requested_provider: string;
  provider_routing: "exact" | "automatic";
}

const routingLabel = (values: ProviderRouteValues): string =>
  values.provider_routing === "automatic"
    ? "OpenRouter automatic routing"
    : `Exact provider · ${values.requested_provider}`;

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

const supportRows = computed<SupportRow[]>(() => [
  {
    role: "Primary Oracle",
    description: "Searches evidence and proposes an answer.",
    values: props.episode.oracle_support.oracle,
  },
  {
    role: "Reviewer",
    description: "Checks each Oracle YES or NO independently.",
    values: props.episode.oracle_support.reviewer,
  },
  {
    role: "Judge",
    description: "Decides when the Oracle and Reviewer disagree.",
    values: props.episode.oracle_support.judge,
  },
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
          <h2 id="technical-heading">Models and usage.</h2>
        </div>
        <p>
          Models, prompt versions, tokens, cache use, latency, and recorded cost for this
          episode.
        </p>
      </header>

      <div class="technical-context">
        <article>
          <span>Hidden subject</span>
          <strong>{{ episode.subject_name }}</strong>
          <p>{{ episode.subject_description }}</p>
          <a
            v-if="episode.subject_reference_url"
            :href="episode.subject_reference_url"
            target="_blank"
            rel="noreferrer"
          >
            Subject reference <span aria-hidden="true">↗</span>
            <span class="visually-hidden">(opens in a new tab)</span>
          </a>
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

      <div class="model-grid">
        <article
          v-for="model in episode.models"
          :key="`${model.role}-${model.requested_model}`"
          :class="{ tested: model.role === 'guesser' }"
        >
          <span>
            {{
              model.role === "guesser"
                ? "Model under test · Guesser · scored"
                : `Benchmark support · ${statusLabel(model.role)} · not scored`
            }}
          </span>
          <h3>{{ model.requested_model }}</h3>
          <p>
            {{ model.requested_provider }} ·
            {{ reasoningEffortLabel(model.reasoning_effort) }} reasoning
          </p>
          <dl>
            <div>
              <dt>Resolved model</dt>
              <dd>{{ model.resolved_models.join(", ") || "Not reported" }}</dd>
            </div>
            <div>
              <dt>Resolved provider</dt>
              <dd>{{ model.resolved_providers.join(", ") || "Not reported" }}</dd>
            </div>
            <div><dt>Routing</dt><dd>{{ routingLabel(model) }}</dd></div>
            <div>
              <dt>Prompt contract</dt>
              <dd><code>{{ model.prompt_version }}</code></dd>
            </div>
            <div>
              <dt>Configuration</dt>
              <dd><code>{{ model.configuration_id ?? "role-local" }}</code></dd>
            </div>
          </dl>
          <details class="provider-routing-details">
            <summary>Resolved provider details</summary>
            <p
              v-if="
                model.providers.length === 0 &&
                model.unreported_calls === 0
              "
            >
              <template v-if="model.resolved_providers.length > 0">
                Legacy run. Per-call routing totals were not retained. Recorded
                resolved provider:
                <strong>{{ model.resolved_providers.join(", ") }}</strong>.
              </template>
              <template v-else>
                No resolved provider was recorded for this role.
              </template>
            </p>
            <template v-else>
              <div
                v-for="provider in model.providers"
                :key="provider.provider"
                class="provider-routing-row"
              >
                <strong>{{ provider.provider }}</strong>
                <span>{{ integer(provider.calls) }} calls</span>
                <span>{{ moneyEpisode(provider.cost_usd) }}</span>
                <span>{{ seconds(provider.latency_ms) }} s</span>
              </div>
              <dl class="provider-routing-totals">
                <div>
                  <dt>Fallback calls</dt>
                  <dd>{{ integer(model.fallback_calls) }}</dd>
                </div>
                <div>
                  <dt>Provider unreported</dt>
                  <dd>{{ integer(model.unreported_calls) }}</dd>
                </div>
              </dl>
            </template>
          </details>
        </article>
      </div>

      <section class="support-section" aria-labelledby="support-heading">
        <header>
          <p class="eyebrow">Oracle support</p>
          <h3 id="support-heading">Blind review roles.</h3>
        </header>
        <div class="support-grid">
          <article v-for="row in supportRows" :key="row.role">
            <span>{{ row.role }}</span>
            <strong>{{ row.values.requested_model }}</strong>
            <p>{{ row.description }}</p>
            <dl>
              <div><dt>Calls</dt><dd>{{ row.values.calls }}</dd></div>
              <div><dt>Cost</dt><dd>{{ moneyEpisode(row.values.cost_usd) }}</dd></div>
              <div>
                <dt>Reasoning</dt>
                <dd>{{ reasoningEffortLabel(row.values.reasoning_effort) }}</dd>
              </div>
              <div><dt>Routing</dt><dd>{{ routingLabel(row.values) }}</dd></div>
            </dl>
            <details class="provider-routing-details">
              <summary>Resolved provider details</summary>
              <p v-if="row.values.calls === 0">
                This role was not invoked in this episode.
              </p>
              <p
                v-else-if="
                  row.values.providers.length === 0 &&
                  row.values.unreported_calls === 0
                "
              >
                Legacy run. Per-call routing totals were not retained.
                <template v-if="row.values.provider_routing === 'exact'">
                  The configured provider was
                  <strong>{{ row.values.requested_provider }}</strong>.
                </template>
              </p>
              <template v-else>
                <div
                  v-for="provider in row.values.providers"
                  :key="provider.provider"
                  class="provider-routing-row"
                >
                  <strong>{{ provider.provider }}</strong>
                  <span>{{ integer(provider.calls) }} calls</span>
                  <span>{{ moneyEpisode(provider.cost_usd) }}</span>
                  <span>{{ seconds(provider.latency_ms) }} s</span>
                </div>
                <dl class="provider-routing-totals">
                  <div>
                    <dt>Fallback calls</dt>
                    <dd>{{ integer(row.values.fallback_calls) }}</dd>
                  </div>
                  <div>
                    <dt>Provider unreported</dt>
                    <dd>{{ integer(row.values.unreported_calls) }}</dd>
                  </div>
                </dl>
              </template>
            </details>
          </article>
        </div>
      </section>

      <div
        class="table-wrap telemetry-wrap"
        tabindex="0"
        aria-label="Scrollable component telemetry"
      >
        <table class="data-table telemetry-table">
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
          <div><dt>Started</dt><dd>{{ dateTime(episode.started_at) }}</dd></div>
          <div><dt>Completed</dt><dd>{{ dateTime(episode.completed_at) }}</dd></div>
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

.technical-context,
.model-grid,
.support-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin-bottom: 1.2rem;
  border: var(--rule-default);
  background: var(--border-default);
}

.technical-context article,
.model-grid article,
.support-grid article {
  min-width: 0;
  padding: 1.2rem;
  background: var(--surface-raised);
}

.technical-context article > span,
.model-grid article > span,
.model-grid dt,
.support-grid article > span,
.support-grid dt,
.provenance-details dt {
  color: var(--text-secondary);
  font-size: var(--text-caption);
  font-weight: 780;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.technical-context strong,
.support-grid strong {
  display: block;
  margin-top: 0.65rem;
  font-size: 0.92rem;
}

.technical-context p,
.model-grid p,
.support-grid p {
  color: var(--text-secondary);
  font-size: var(--text-micro);
  line-height: 1.6;
}

.technical-context a {
  color: var(--blue-ink);
  font-size: var(--text-micro);
  font-weight: 720;
}

.model-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.model-grid article.tested {
  box-shadow: inset var(--border-emphasis-width) 0 0 var(--blue);
}

.model-grid h3 {
  margin: 0.7rem 0 0;
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 500;
  letter-spacing: -0.035em;
}

.model-grid dl,
.support-grid dl {
  margin: 1rem 0 0;
}

.model-grid dl div,
.support-grid dl div {
  display: grid;
  grid-template-columns: 7rem minmax(0, 1fr);
  gap: 0.8rem;
  padding-top: 0.55rem;
}

.model-grid dd,
.support-grid dd {
  min-width: 0;
  margin: 0;
  font-size: var(--text-micro);
  overflow-wrap: anywhere;
}

.support-section {
  margin-top: 2rem;
}

.support-section > header h3 {
  margin: 0 0 1rem;
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 500;
}

.provider-routing-details {
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: var(--rule-default);
}

.provider-routing-details summary {
  cursor: pointer;
  color: var(--blue-ink);
  font-size: var(--text-micro);
  font-weight: 720;
}

.provider-routing-details p strong {
  display: inline;
  margin: 0;
  font-size: inherit;
}

.provider-routing-row {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
  align-items: baseline;
  padding: 0.7rem 0;
  border-bottom: var(--rule-default);
  font-size: var(--text-micro);
}

.provider-routing-row strong {
  margin: 0;
  overflow-wrap: anywhere;
}

.provider-routing-row span {
  color: var(--text-secondary);
}

.provider-routing-totals {
  margin-top: 0.4rem !important;
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
  .technical-context,
  .model-grid,
  .support-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .provider-routing-row {
    grid-template-columns: 1fr 1fr;
  }

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
