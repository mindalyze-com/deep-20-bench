<script setup lang="ts">
import { computed } from "vue";

import { runRoleCopy } from "@/lib/run-roles";
import type { PublicRunModel } from "@/lib/types";

import RunModelCard from "./RunModelCard.vue";

const props = defineProps<{
  models: PublicRunModel[];
}>();

const guesser = computed(
  () => props.models.find((model) => model.role === "guesser") ?? null,
);
const supportModels = computed(() =>
  props.models.filter((model) => model.role !== "guesser"),
);
</script>

<template>
  <section class="run-models" aria-labelledby="run-models-title">
    <header class="run-models-heading">
      <div>
        <p class="eyebrow">Run configuration</p>
        <h2 id="run-models-title">Models.</h2>
      </div>
      <p>
        Model identity, prompt versions, routing, calls, and recorded cost for the full
        run.
      </p>
    </header>

    <div v-if="guesser" class="guesser-model">
      <RunModelCard
        :model="guesser"
        :role-label="runRoleCopy.guesser.roleLabel"
        :description="runRoleCopy.guesser.description"
        featured
      />
    </div>

    <section class="support-section" aria-labelledby="support-models-title">
      <header class="support-heading">
        <div>
          <p class="eyebrow">Game support</p>
          <h3 id="support-models-title">Oracle and adjudication.</h3>
        </div>
        <p>
          These models support the game. They are fixed across the run and are not under
          test.
        </p>
      </header>

      <div class="support-model-grid">
        <RunModelCard
          v-for="model in supportModels"
          :key="model.role"
          :model="model"
          :role-label="runRoleCopy[model.role].roleLabel"
          :description="runRoleCopy[model.role].description"
        />
      </div>
    </section>
  </section>
</template>

<style scoped>
.run-models {
  margin-top: clamp(2.5rem, 6vw, 5rem);
  padding-top: clamp(2rem, 4vw, 3.5rem);
  border-top: var(--rule-strong);
}

.run-models-heading,
.support-heading {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(17rem, 0.55fr);
  gap: 2rem;
  align-items: end;
}

.run-models-heading {
  margin-bottom: clamp(1.5rem, 3vw, 2.25rem);
}

.run-models-heading h2,
.support-heading h3 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.045em;
  line-height: 1;
}

.run-models-heading h2 {
  font-size: var(--text-section-title);
}

.support-heading h3 {
  font-size: var(--text-card-title);
}

.run-models-heading > p,
.support-heading > p {
  margin: 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.6;
}

.support-section {
  margin-top: -1px;
}

.support-heading {
  padding: var(--workspace-panel-padding);
  border: var(--rule-default);
  background: var(--surface-rail);
}

.support-model-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin-top: -1px;
}

.support-model-grid > :nth-child(even) {
  margin-left: -1px;
}

.support-model-grid > :nth-child(n + 3) {
  margin-top: -1px;
}

@media (min-width: 761px) and (max-width: 900px) {
  .support-model-grid {
    grid-template-columns: 1fr;
  }

  .support-model-grid > :nth-child(even) {
    margin-left: 0;
  }

  .support-model-grid > * + * {
    margin-top: -1px;
  }
}

@media (max-width: 760px) {
  .run-models {
    margin-top: 2.5rem;
    padding-top: 2rem;
  }

  .run-models-heading,
  .support-heading {
    grid-template-columns: 1fr;
    gap: 0.8rem;
  }

  .support-model-grid {
    grid-template-columns: 1fr;
  }

  .support-model-grid > :nth-child(even) {
    margin-left: 0;
  }

  .support-model-grid > * + * {
    margin-top: -1px;
  }
}
</style>
