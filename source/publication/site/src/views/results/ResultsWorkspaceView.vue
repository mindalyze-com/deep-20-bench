<script setup lang="ts">
import { computed, nextTick, onActivated, watch } from "vue";
import { useRoute } from "vue-router";

import EmptyEditionResults from "@/components/EmptyEditionResults.vue";
import { useEditionContext } from "@/lib/use-edition-context";
import ResultsNav from "@/components/ResultsNav.vue";

const route = useRoute();
const { manifest, cohort, editionId } = useEditionContext();
const isResultsWorkspaceRoute = computed(() =>
  route.matched.some((record) => record.path.endsWith("/results/")),
);
const resetResultsScroll = async (): Promise<void> => {
  await nextTick();
  window.scrollTo({ top: 0, left: 0 });
};

onActivated(() => {
  void resetResultsScroll();
});
watch(
  () => route.name,
  () => {
    void resetResultsScroll();
  },
  { flush: "post" },
);

const copy = computed(() => {
  switch (route.name) {
    case "results-reliability":
      return {
        label: "Repeated-trial stability",
        title: "Stability",
        description:
          "Whether a model produces similar scores across repeated trials on the same fixed subjects.",
        tone: "stability",
      };
    case "results-cost":
      return {
        label: "Recorded costs",
        title: "Cost",
        description:
          "Recorded provider costs for the tested model and benchmark support models.",
        tone: "cost",
      };
    case "results-time":
      return {
        label: "Model and benchmark time",
        title: "Time",
        description:
          "Provider-reported model-call time and end-to-end benchmark runtime.",
        tone: "time",
      };
    case "results-efficiency":
      return {
        label: "Cost and quality",
        title: "Efficiency",
        description:
          "Compare question quality with the recorded cost of the model under test.",
        tone: "efficiency",
      };
    default:
      return {
        label: "Official comparison",
        title: "Results",
        description:
          "Question score, stability, cost, and time for the current official runs.",
        tone: "score",
      };
  }
});
</script>

<template>
  <div
    id="route-content"
    class="results-workspace"
    :class="`results-workspace--${copy.tone}`"
    tabindex="-1"
  >
    <header class="results-workspace-header site-boundary-shell">
      <div class="results-workspace-header-inner site-boundary">
        <div>
          <p class="eyebrow">{{ copy.label }}</p>
          <h1>{{ copy.title }} <span class="results-edition">{{ cohort?.edition_label }}</span></h1>
        </div>
        <p>{{ copy.description }}</p>
        <ResultsNav />
      </div>
    </header>

    <div class="results-workspace-body">
      <div v-if="manifest?.official_runs.length === 0" class="site-boundary-shell edition-empty-container"><div class="site-boundary"><EmptyEditionResults /></div></div>
      <RouterView v-else-if="isResultsWorkspaceRoute" v-slot="{ Component }">
        <KeepAlive>
          <component :is="Component" :key="`${editionId}:${String(route.name)}`" />
        </KeepAlive>
      </RouterView>
    </div>
  </div>
</template>

<style scoped>
.results-edition { font-family: var(--font-body); font-size: .45em; color: var(--text-secondary); letter-spacing: 0; }
.results-workspace {
  --result-accent: var(--blue);
  --result-accent-ink: var(--blue-ink);
  --result-accent-soft: var(--surface-accent-soft);

  min-height: 60vh;
  background: var(--paper);
}

.results-workspace--stability {
  --result-accent: var(--result-stability);
  --result-accent-ink: var(--result-stability-ink);
  --result-accent-soft: var(--result-stability-soft);
}

.results-workspace--cost {
  --result-accent: var(--coral);
  --result-accent-ink: var(--state-danger-ink);
  --result-accent-soft: var(--surface-danger-soft);
}

.results-workspace--time {
  --result-accent: var(--chart-acid);
  --result-accent-ink: var(--result-time-ink);
  --result-accent-soft: var(--surface-success-soft);
}

.results-workspace--efficiency {
  --result-accent: var(--result-efficiency);
  --result-accent-ink: var(--result-efficiency-ink);
  --result-accent-soft: var(--result-efficiency-soft);
}

.results-workspace-header {
  padding-top: 1rem;
  border-bottom: var(--rule-default);
  background: var(--paper-bright);
}

.results-workspace-header-inner {
  display: grid;
  grid-template-columns: minmax(12rem, 0.45fr) minmax(16rem, 0.55fr) auto;
  gap: clamp(1.5rem, 4vw, 4rem);
  align-items: end;

}

.results-workspace-header-inner > div { padding-bottom: .9rem; }

.results-workspace-header .eyebrow {
  margin-bottom: 0.25rem;
  color: var(--result-accent-ink);
}

.results-workspace :deep(.results-view .eyebrow) {
  color: var(--result-accent-ink);
}

.results-workspace-header h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.5rem, 4vw, 4rem);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.055em;
  line-height: 0.9;
}

.results-workspace-header-inner > p {
  max-width: 30rem;
  margin: 0 0 1rem;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.55;
}

.results-workspace-header :deep(.results-nav) {
  align-self: stretch;
  border-bottom: 0;
  background: transparent;
  padding-inline: 0;
}

.results-workspace-header :deep(.results-nav a) {
  display: inline-flex;
  align-items: end;
  padding-block: .8rem 1rem;
}

.edition-empty-container { padding-block: 1.5rem 3rem; }

.results-workspace-body {
  min-height: 1px;
}

.results-workspace-body :deep(.results-view) {
  min-height: 1px;
}

.results-workspace-body :deep(.results-view > .content-section) {
  padding-block: clamp(1.4rem, 3vw, 3rem);
}

@media (max-width: 1200px) {
  .results-workspace-header {
    min-height: 0;
  }

  .results-workspace-header-inner {
    grid-template-columns: auto minmax(0, 1fr);
    gap: .35rem 2rem;
    min-height: 0;
  }

  .results-workspace-header :deep(.results-nav) {
    grid-column: 1 / -1;
    order: 3;
  }

  .results-workspace-header-inner > p {
    margin-bottom: .9rem;
  }
}

@media (max-width: 760px) {
  .results-workspace {
    min-height: 100%;
  }

  .results-workspace-header {
    padding-top: 0.85rem;
  }

  .results-workspace-header-inner {
    grid-template-columns: 1fr;
    gap: 0.35rem;
  }

  .results-workspace-header-inner > div { padding-bottom: .25rem; }

  .results-workspace-header h1 {
    font-size: 2.65rem;
  }

  .results-workspace-header-inner > p {
    display: none;
  }

  .results-workspace-header :deep(.results-nav) {
    grid-column: 1;
  }

  .results-workspace-header :deep(.results-nav a) {
    min-width: 44px;
    padding: 0.8rem 0.45rem;
    justify-content: center;
  }

}
</style>
