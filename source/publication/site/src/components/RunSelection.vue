<script setup lang="ts">
import { useRunSelection } from "@/lib/run-selection";
const { allRuns, select } = useRunSelection();
</script>
<template>
  <div class="run-selection site-boundary" aria-label="Run selection">
    <div class="run-selection-buttons" role="group" aria-label="Displayed runs">
      <button :aria-pressed="!allRuns" @click="select(false)">Latest per model</button>
      <button :aria-pressed="allRuns" @click="select(true)">All dated runs</button>
    </div>
    <p>{{ allRuns ? "Each date is a separate result. Earlier runs keep their own scores and have no current model rank." : "One complete run per model. Open a model to see its earlier test dates." }}</p>
  </div>
</template>
<style scoped>
.run-selection { display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; padding-block: 0.8rem; }
.run-selection-buttons { display: inline-flex; flex-shrink: 0; border: var(--rule-default); border-radius: 6px; padding: 3px; gap: 3px; background: var(--paper-bright); }
button { min-height: 44px; border: 0; border-radius: 3px; padding: 0.5rem 0.85rem; font: inherit; font-size: 0.8125rem; background: transparent; cursor: pointer; color: var(--text-secondary); }
button[aria-pressed="true"] { background: var(--ink, #1b2322); color: white; }
p { font-size: 0.8125rem; color: var(--text-secondary); margin: 0; max-width: 48rem; }
</style>
