<script setup lang="ts">
import { computed, nextTick, onActivated, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ResultsNav from "@/components/ResultsNav.vue";

const route = useRoute();
const resultsBody = ref<HTMLElement | null>(null);

const resetResultsScroll = async (): Promise<void> => {
  await nextTick();
  const viewport = resultsBody.value?.closest<HTMLElement>(".app-viewport");
  if (viewport !== undefined && viewport !== null) {
    viewport.scrollTop = 0;
    viewport.scrollLeft = 0;
  }
  const scroller = resultsBody.value?.querySelector<HTMLElement>(".results-view");
  if (scroller === undefined || scroller === null) return;
  scroller.scrollTop = 0;
  scroller.scrollLeft = 0;
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
    case "results-cost":
      return {
        label: "Recorded spend",
        title: "Cost",
        description: "Full-run and per-episode provider costs.",
      };
    case "results-time":
      return {
        label: "Guesser latency",
        title: "Time",
        description: "Provider-reported response time for the model under test.",
      };
    case "results-efficiency":
      return {
        label: "Cost × quality",
        title: "Efficiency",
        description: "Question score adjusted by recorded Guesser cost.",
      };
    default:
      return {
        label: "Official comparison",
        title: "Results",
        description: "Quality, reliability, cost, and time for one active cohort.",
      };
  }
});
</script>

<template>
  <div id="route-content" class="results-workspace" tabindex="-1">
    <header class="results-workspace-header">
      <div>
        <p class="eyebrow">{{ copy.label }}</p>
        <h1>{{ copy.title }}</h1>
      </div>
      <p>{{ copy.description }}</p>
      <ResultsNav />
    </header>

    <div ref="resultsBody" class="results-workspace-body">
      <RouterView v-slot="{ Component }">
        <KeepAlive>
          <component :is="Component" />
        </KeepAlive>
      </RouterView>
    </div>
  </div>
</template>

<style scoped>
.results-workspace {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--paper);
}

.results-workspace-header {
  display: grid;
  grid-template-columns: minmax(12rem, 0.45fr) minmax(16rem, 0.55fr) auto;
  gap: clamp(1.5rem, 4vw, 4rem);
  align-items: end;
  min-height: 112px;
  padding: 1.2rem var(--gutter) 0;
  border-bottom: 1px solid var(--line);
  background: var(--paper-bright);
}

.results-workspace-header .eyebrow {
  margin-bottom: 0.25rem;
  color: var(--blue-ink);
}

.results-workspace-header h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.5rem, 4vw, 4rem);
  font-weight: 500;
  letter-spacing: -0.055em;
  line-height: 0.9;
}

.results-workspace-header > p {
  max-width: 30rem;
  margin: 0 0 1.15rem;
  color: var(--muted);
  font-size: 0.77rem;
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
  padding-bottom: 1.2rem;
}

.results-workspace-body {
  min-height: 0;
  overflow: hidden;
}

.results-workspace-body :deep(.results-view) {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.results-workspace-body :deep(.results-view > .results-hero),
.results-workspace-body :deep(.results-view > .results-nav) {
  display: none;
}

.results-workspace-body :deep(.results-view > .content-section) {
  padding-block: clamp(1.4rem, 3vw, 3rem);
}

@media (max-width: 900px) {
  .results-workspace-header {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 1rem 2rem;
    min-height: 0;
  }

  .results-workspace-header :deep(.results-nav) {
    grid-column: 1 / -1;
    order: 3;
  }

  .results-workspace-header > p {
    margin-bottom: 0;
  }
}

@media (max-width: 760px) {
  .results-workspace {
    display: block;
    height: auto;
    min-height: 100%;
    overflow: visible;
  }

  .results-workspace-header {
    grid-template-columns: 1fr;
    gap: 0.35rem;
    padding-top: 0.85rem;
  }

  .results-workspace-header h1 {
    font-size: 2.65rem;
  }

  .results-workspace-header > p {
    display: none;
  }

  .results-workspace-header :deep(.results-nav) {
    grid-column: 1;
  }

  .results-workspace-header :deep(.results-nav a) {
    padding-block: 0.8rem;
  }

  .results-workspace-body {
    overflow: visible;
  }

  .results-workspace-body :deep(.results-view) {
    height: auto;
    overflow: visible;
    scrollbar-gutter: auto;
  }
}
</style>
