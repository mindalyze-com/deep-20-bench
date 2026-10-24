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
  // The app restores the comparison's saved position when returning from a detail page.
  if (!isResultsWorkspaceRoute.value || route.name === "results-compare") return;
  await nextTick();
  if (isResultsWorkspaceRoute.value && route.name !== "results-compare") window.scrollTo({ top: 0, left: 0 });
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
    case "results-compare":
      return { title: "Compare models", tone: "score" };
    case "results-reliability":
      return {
        title: "Score stability",
        tone: "stability",
      };
    case "results-cost":
      return {
        title: "Model cost",
        tone: "cost",
      };
    case "results-time":
      return {
        title: "Model time",
        tone: "time",
      };
    case "results-efficiency":
      return {
        title: "Cost efficiency",
        tone: "efficiency",
      };
    default:
      return {
        title: "AI leaderboard",
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
        <div class="results-heading">
          <h1>{{ copy.title }} <span class="results-edition">{{ cohort?.edition_label }}</span></h1>
        </div>
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

/* Every result view shares the same compact header and responsive layout. */
.results-workspace-header {
  --results-nav-font-size: 0.875rem;

  border-bottom: var(--rule-default);
  background: var(--paper-bright);
}

.results-workspace-header-inner {
  display: flex;
  flex-wrap: nowrap;
  gap: 1.5rem;
  align-items: center;
  justify-content: space-between;
}

.results-heading {
  flex-shrink: 0;
  min-width: 0;
}

.results-workspace-header h1 {
  display: flex;
  gap: 0.65rem;
  align-items: center;
  margin: 0;
  font-family: var(--font-body);
  font-size: var(--results-nav-font-size);
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.035em;
  line-height: 1.2;
  white-space: nowrap;
}

.results-workspace-header .results-edition {
  display: inline-flex;
  align-items: center;
  min-height: 1.5rem;
  padding: 0.15rem 0.45rem;
  border: var(--rule-default);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium);
  letter-spacing: 0;
  line-height: 1;
}

.results-workspace-header :deep(.results-nav) {
  flex-shrink: 1;
  align-self: stretch;
  align-items: end;
  padding-inline: 0;
  border-bottom: 0;
  background: transparent;
}

.results-workspace-header :deep(.results-nav a) {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 0.9rem;
  font-size: var(--results-nav-font-size);
}

.results-workspace :deep(.results-view .eyebrow) {
  color: var(--result-accent-ink);
}

.edition-empty-container { padding-block: 1.5rem 3rem; }

.results-workspace-body,
.results-workspace-body :deep(.results-view) {
  min-height: 1px;
}

.results-workspace-body :deep(.results-view > .content-section) {
  padding-block: clamp(1.25rem, 2vw, 2rem);
  padding-top: 0.75rem;
}

@media (max-width: 760px) {
  .results-workspace { min-height: 100%; }

  .results-workspace-header {
    --results-nav-font-size: 0.8125rem;
  }

  /* Keep the page heading accessible without reserving a mobile title row. */
  .results-heading {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }

  .results-workspace-header :deep(.results-nav) {
    width: 100%;
  }

  .results-workspace-header :deep(.results-nav a) {
    min-width: 44px;
    padding: 0.65rem 0.7rem;
    justify-content: center;
    font-size: var(--results-nav-font-size);
  }
}
</style>
