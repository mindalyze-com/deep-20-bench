<script setup lang="ts">
import { computed, ref, shallowRef, watch } from "vue";
import { getManifest, peekManifest } from "@/lib/api";
import { answerLabel, editionAnswers } from "@/lib/use-edition-context";
import { editionRoute } from "@/lib/route-location";
import type { CohortConfig } from "@/lib/types";

const props = defineProps<{ editionId: string }>();
const cohort = shallowRef<CohortConfig | null>(null);
const failed = ref(false);
const answers = computed(() => editionAnswers(cohort.value));

watch(() => props.editionId, async (editionId, _previous, onCleanup) => {
  let active = true;
  onCleanup(() => { active = false; });
  cohort.value = peekManifest(editionId)?.active_cohort ?? null;
  failed.value = false;
  if (cohort.value !== null || import.meta.env.SSR) return;
  try {
    const manifest = await getManifest(editionId);
    if (active) cohort.value = manifest.active_cohort;
  } catch {
    if (active) failed.value = true;
  }
}, { immediate: true });

defineEmits<{ navigate: [] }>();
</script>
<template>
  <div class="edition-summary" :aria-busy="cohort === null && !failed">
    <p class="edition-label">Edition {{ editionId }} settings</p>
    <template v-if="cohort">
    <div class="edition-facts" :aria-label="`Edition ${cohort.edition_id} settings`">
      <span><strong>{{ cohort.target_ids.length }}</strong> subjects</span>
      <span><strong>{{ cohort.iterations }}</strong> rounds per subject</span>
      <span><strong>{{ cohort.max_questions }}</strong> question limit</span>
    </div>
    <div class="edition-answers">
      <span>Question answers</span>
      <span v-for="answer in answers" :key="answer" class="answer-token" :class="`answer-token--${answer.toLowerCase()}`">{{ answerLabel(answer) }}</span>
    </div>
    </template>
    <p v-else class="edition-summary-status" role="status">{{ failed ? 'Settings could not be loaded.' : 'Loading settings…' }}</p>
    <RouterLink class="edition-changes" :to="editionRoute('methodology', { editionId, hash: '#editions' })" @click="$emit('navigate')">
      What changed <span aria-hidden="true">→</span>
    </RouterLink>
  </div>
</template>
<style scoped>
.edition-summary { margin-top: .75rem; padding: .95rem .75rem 0; border-top: var(--rule-subtle); color: var(--text-primary); }
.edition-label { margin: 0 0 .75rem; font-size: var(--text-micro); color: var(--text-secondary); font-weight: var(--font-weight-semibold); }
.edition-summary-status { min-height: 8rem; margin: 0; color: var(--text-secondary); font-size: var(--text-caption); }
.edition-facts { display: grid; grid-template-columns: .85fr 1.2fr 1fr; gap: .75rem; font-size: var(--text-micro); color: var(--text-secondary); line-height: 1.4; }
.edition-facts strong { display: block; margin-bottom: .15rem; color: var(--text-primary); font-size: 1.35rem; font-weight: var(--font-weight-semibold); font-variant-numeric: tabular-nums; }
.edition-answers { display: flex; flex-wrap: wrap; align-items: center; gap: .3rem; padding-block: .85rem; font-size: var(--text-micro); }
.edition-answers > span:first-child { flex-basis: 100%; margin-bottom: .2rem; color: var(--text-secondary); }
.answer-token { padding: .25rem .4rem; background: var(--surface-rail); border: 1px solid var(--border-inverse-subtle); border-radius: 4px; }
.answer-token--yes, .answer-token--rather_yes { color: var(--state-clean-ink); background: var(--surface-success-soft); }
.answer-token--no, .answer-token--rather_no { color: var(--state-danger-ink); background: var(--surface-danger-soft); }
.answer-token--yes, .answer-token--no { font-weight: var(--font-weight-bold); }
.edition-changes { display: flex; align-items: center; justify-content: space-between; min-height: 44px; border-top: var(--rule-subtle); color: var(--blue-ink); font-size: var(--text-caption); text-decoration: none; }
.edition-changes:hover { text-decoration: underline; }
</style>
