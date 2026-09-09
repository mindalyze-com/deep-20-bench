<script setup lang="ts">
import { computed } from "vue";
import { useEditionContext } from "@/lib/use-edition-context";
const { cohort, editionsIndex } = useEditionContext();
const other = computed(() => editionsIndex.value?.editions.find(edition =>
  edition.edition_id !== cohort.value?.edition_id && edition.runs.length > 0));
</script>
<template>
  <section v-if="cohort" class="edition-empty" aria-label="No complete edition results">
    <div>
      <p class="eyebrow">Edition {{ cohort.edition_label }}</p>
      <h2>No complete {{ cohort.edition_label }} results yet</h2>
      <p>A model result appears after all {{ cohort.target_ids.length * cohort.iterations }} rounds
        have completed. Earlier diagnostic games remain outside this ranking.</p>
    </div>
    <RouterLink v-if="other" class="button button-primary"
      :to="{ name: 'results', params: { editionId: other.edition_id } }">
      View version {{ other.label }} results →
    </RouterLink>
  </section>
</template>
<style scoped>
.edition-empty { display: flex; align-items: center; flex-wrap: wrap; gap: 1.5rem 2.5rem; padding: clamp(1.25rem, 3vw, 2.5rem); background: var(--surface-raised); border-top: 3px solid var(--blue); }
.edition-empty > div { flex: 1 1 25rem; }
h2 { margin: .35rem 0 .75rem; font-family: var(--font-display); font-size: clamp(1.8rem, 3vw, 2.6rem); font-weight: var(--font-weight-medium); line-height: 1.15; }
p { margin: 0; color: var(--text-secondary); font-size: var(--text-small); max-width: 40rem; }
</style>
