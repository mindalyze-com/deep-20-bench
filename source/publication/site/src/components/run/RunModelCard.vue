<script setup lang="ts">
import { integer, moneyEpisode, reasoningEffortLabel, seconds } from "@/lib/format";
import type { PublicRunModel } from "@/lib/types";

const props = defineProps<{
  model: PublicRunModel;
  roleLabel: string;
  description: string;
  featured?: boolean;
}>();

const routingLabel = (): string =>
  props.model.provider_routing === "automatic"
    ? "OpenRouter automatic routing"
    : `Exact provider · ${props.model.requested_provider}`;
</script>

<template>
  <article class="run-model-card" :class="{ featured }">
    <header class="run-model-card-header">
      <span class="run-model-role">{{ roleLabel }}</span>
      <span v-if="featured" class="model-test-sticker">Model under test</span>
    </header>

    <div class="run-model-identity">
      <h3>{{ model.requested_model }}</h3>
      <p>{{ description }}</p>
    </div>

    <dl class="run-model-facts">
      <div><dt>Calls</dt><dd>{{ integer(model.calls) }}</dd></div>
      <div><dt>Cost</dt><dd>{{ moneyEpisode(model.cost_usd) }}</dd></div>
      <div>
        <dt>Reasoning</dt>
        <dd>{{ reasoningEffortLabel(model.reasoning_effort) }}</dd>
      </div>
      <div><dt>Routing</dt><dd>{{ routingLabel() }}</dd></div>
      <div v-if="model.resolved_models.length > 0">
        <dt>Resolved model</dt>
        <dd>{{ model.resolved_models.join(", ") }}</dd>
      </div>
      <div v-if="model.resolved_providers.length > 0">
        <dt>Resolved provider</dt>
        <dd>{{ model.resolved_providers.join(", ") }}</dd>
      </div>
      <div v-if="model.prompt_version !== null">
        <dt>Prompt contract</dt>
        <dd><code>{{ model.prompt_version }}</code></dd>
      </div>
      <div v-if="model.configuration_id !== null">
        <dt>Configuration</dt>
        <dd><code>{{ model.configuration_id }}</code></dd>
      </div>
    </dl>

    <details class="provider-routing-details">
      <summary>Resolved provider details</summary>
      <p v-if="model.calls === 0">This role was not invoked in this run.</p>
      <p
        v-else-if="model.providers.length === 0 && model.unreported_calls === 0"
      >
        Legacy run. Per-call routing totals were not retained. The configured provider
        was <strong>{{ model.requested_provider }}</strong>.
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
</template>

<style scoped>
.run-model-card {
  display: flex;
  min-width: 0;
  padding: var(--workspace-panel-padding);
  border: var(--rule-default);
  flex-direction: column;
  background: var(--paper-bright);
}

.run-model-card.featured {
  display: grid;
  grid-template-columns: minmax(15rem, 0.8fr) minmax(0, 1.2fr);
  column-gap: clamp(2rem, 5vw, 5rem);
  border-top: var(--border-emphasis-width) solid var(--blue);
}

.run-model-card-header {
  display: flex;
  min-height: 1.6rem;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.featured .run-model-card-header {
  grid-column: 1 / -1;
  margin-bottom: 1rem;
}

.run-model-role,
.run-model-facts dt,
.provider-routing-totals dt {
  color: var(--muted);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.model-test-sticker {
  flex: 0 0 auto;
  padding: 0.22rem 0.42rem 0.18rem;
  border: var(--rule-strong);
  background: var(--acid);
  color: var(--ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-extrabold);
  letter-spacing: 0.045em;
  line-height: 1.2;
  text-transform: uppercase;
  transform: rotate(-1deg);
}

.run-model-identity h3 {
  margin: 0.7rem 0 0;
  font-family: var(--font-display);
  font-size: clamp(1.45rem, 2vw, 1.9rem);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.04em;
  line-height: 1.05;
  overflow-wrap: anywhere;
}

.featured .run-model-identity h3 {
  max-width: 16ch;
  margin-top: 0;
  font-size: clamp(2.2rem, 4vw, 3.4rem);
  letter-spacing: -0.055em;
  line-height: 0.95;
}

.run-model-identity p,
.provider-routing-details p {
  color: var(--muted);
  font-size: var(--text-micro);
  line-height: 1.6;
}

.run-model-identity p {
  min-height: 3.2em;
  margin: 0.7rem 0 0;
}

.featured .run-model-identity p {
  max-width: 28rem;
  min-height: 0;
  font-size: 0.88rem;
}

.run-model-facts {
  margin: 1rem 0 0;
}

.featured .run-model-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 1.5rem;
  margin-top: 0;
}

.run-model-facts > div {
  display: grid;
  grid-template-columns: 6.5rem minmax(0, 1fr);
  gap: 0.8rem;
  padding-top: 0.55rem;
}

.run-model-facts dd {
  min-width: 0;
  margin: 0;
  font-size: var(--text-micro);
  overflow-wrap: anywhere;
}

.provider-routing-details {
  margin-top: auto;
  padding-top: 0.9rem;
}

.featured .provider-routing-details {
  grid-column: 1 / -1;
  margin-top: 1.5rem;
}

.provider-routing-details summary {
  cursor: pointer;
  color: var(--blue-ink);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
}

.provider-routing-details summary:focus-visible {
  outline: var(--focus-ring);
  outline-offset: 3px;
}

.provider-routing-row {
  display: grid;
  grid-template-columns: minmax(8rem, 1fr) repeat(3, auto);
  gap: 1rem;
  align-items: baseline;
  padding: 0.65rem 0;
  border-bottom: var(--rule-subtle);
  font-size: var(--text-micro);
}

.provider-routing-row span {
  color: var(--muted);
  white-space: nowrap;
}

.provider-routing-totals {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0.9rem 0 0;
}

.provider-routing-totals div {
  padding: 0.7rem;
  background: var(--surface-page);
}

.provider-routing-totals dd {
  margin: 0.3rem 0 0;
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
}

@media (max-width: 760px) {
  .run-model-card.featured {
    display: flex;
  }

  .featured .run-model-card-header {
    margin-bottom: 0;
  }

  .featured .run-model-identity h3 {
    margin-top: 0.9rem;
    font-size: clamp(2rem, 10vw, 2.8rem);
  }

  .featured .run-model-facts {
    display: block;
    margin-top: 1rem;
  }

  .provider-routing-row {
    grid-template-columns: 1fr 1fr;
    gap: 0.35rem 0.8rem;
  }

  .provider-routing-row span {
    white-space: normal;
  }
}
</style>
