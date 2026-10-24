<script setup lang="ts">
import { computed, nextTick, onActivated, onDeactivated, onMounted, ref, watch } from "vue";
import { onBeforeRouteLeave, useRoute, useRouter, type LocationQueryRaw } from "vue-router";
import ComparisonValue from "@/components/ComparisonValue.vue";
import ComparisonTable from "@/components/ComparisonTable.vue";
import ErrorState from "@/components/ErrorState.vue";
import InfoPopover from "@/components/InfoPopover.vue";
import LoadingState from "@/components/LoadingState.vue";
import ModelName from "@/components/ModelName.vue";
import PublicationTime from "@/components/PublicationTime.vue";
import { getComparison, peekComparison } from "@/lib/api";
import { compareDecimal } from "@/lib/exact-decimal";
import { comparisonScroll, rememberComparisonScroll } from "@/lib/comparison-navigation";
import {
  MAX_COMPARISON_MODELS, compareValue, comparisonState, mainComparisonMetrics,
  queryList, roundMetricFormat, roundValue, scalar, subjectValue, subtractValue, valueMark,
} from "@/lib/comparison";
import { episodeRoute, modelSummaryRoute, runRoute, subjectRoute } from "@/lib/route-location";
import { usePageRouteContext } from "@/lib/route-context";
import type { ComparisonModel } from "@/lib/types";
import { useEditionContext } from "@/lib/use-edition-context";
import { useKeyedPublicationLoad } from "@/lib/use-keyed-publication-load";

const route = useRoute(); const router = useRouter();
const detailQuery = computed(() => ({ compare: route.fullPath }));
const mainScroll = ref<InstanceType<typeof ComparisonTable> | null>(null);
const subjectScroll = ref<InstanceType<typeof ComparisonTable> | null>(null);
const mainOverflow = ref(false); const subjectOverflow = ref(false);
onBeforeRouteLeave((_to, from) => {
  if (typeof window === "undefined") return;
  rememberComparisonScroll(from.fullPath, { top: window.scrollY,
    main: mainScroll.value?.scrollLeft ?? 0, subjects: subjectScroll.value?.scrollLeft ?? 0 });
});
const { editionId } = useEditionContext();
const active = ref(true); const mounted = ref(false); const pickerOpen = ref(true);
onMounted(() => {
  mounted.value = true;
  pickerOpen.value = comparisonState(route.query).modelIds.length === 0;
});
onActivated(() => { active.value = true; });
onDeactivated(() => { active.value = false; });
const { document, loading, error } = useKeyedPublicationLoad({
  parameters: (): [string] => [active.value ? editionId.value : ""],
  clearBeforeLoad: true,
  load: getComparison,
  initial: () => peekComparison(editionId.value),
  fallbackError: "Comparison data could not be loaded.",
});
watch([document, active, mounted, () => route.fullPath], async () => {
  if (!mounted.value || !active.value || document.value === null) return;
  await nextTick();
  const saved = comparisonScroll(route.fullPath);
  if (saved === null || !active.value) return;
  if (mainScroll.value) mainScroll.value.scrollLeft = saved.main;
  if (subjectScroll.value) subjectScroll.value.scrollLeft = saved.subjects;
  // A return after refreshing a detail may need to fetch the comparison again.
  // Restore vertical position once its content exists, even on a slow connection.
  window.scrollTo({ top: saved.top });
}, { flush: "post" });
usePageRouteContext({ title: "Compare models",
  description: "Compare up to five models side by side: score, stability, cost, time, and each round." });

// Static HTML represents the canonical picker. Apply URL selections after hydration.
const state = computed(() => comparisonState(mounted.value ? route.query : {}));
const models = computed(() => document.value?.models ?? []);
const selected = computed(() => state.value.modelIds.flatMap(id => {
  const model = models.value.find(item => item.result.model.model_id === id);
  return model === undefined ? [] : [model];
}));
const selectedNames = computed(() => selected.value.map(model => model.result.model.display_name));
const missing = computed(() => state.value.modelIds.filter(id =>
  !models.value.some(item => item.result.model.model_id === id)));
const tooMany = computed(() => mounted.value && queryList(route.query.models).length > MAX_COMPARISON_MODELS);
const search = ref(""); const copied = ref("");
const shareUrl = ref(""); const shareInput = ref<HTMLInputElement | null>(null);
const shareButton = ref<HTMLButtonElement | null>(null);
const copyButton = ref<HTMLButtonElement | null>(null);
const sharing = ref(false);
const available = computed(() => models.value.filter(model =>
  !state.value.modelIds.includes(model.result.model.model_id) &&
  `${model.result.model.display_name} ${model.result.model.provider}`.toLowerCase().includes(search.value.toLowerCase()))
  .sort((left, right) => left.result.model.display_name.localeCompare(right.result.model.display_name)));
const baseline = computed(() => selected.value.find(model => model.result.model.model_id === state.value.baseline));
const sourceSubjects = computed(() => models.value[0]?.subjects ?? []);
const rounds = computed(() => Array.from({ length: document.value?.iterations ?? 0 }, (_, index) => index + 1));
const subjectFor = (model: ComparisonModel, id: string) => model.subjects.find(subject => subject.target_id === id);
const roundFor = (model: ComparisonModel, id: string, number: number) =>
  subjectFor(model, id)?.rounds.find(round => round.trial_number === number);
const countedQuestionsDiffer = (model: ComparisonModel, id: string, number: number): boolean => {
  const round = roundFor(model, id, number);
  return round?.penalized_questions != null &&
    compareDecimal(round.penalized_questions, String(round.counted_questions)) !== 0;
};
const subjectValues = (id: string) => selected.value.map(model => subjectValue(subjectFor(model, id), state.value.metric));
const roundValues = (id: string, number: number) => selected.value.map(model =>
  roundValue(roundFor(model, id, number), state.value.metric));
const gap = (id: string) => {
  const values = subjectValues(id).filter(value => value !== null).sort(compareValue);
  return values.length < 2 ? scalar(0)! : subtractValue(values[values.length - 1]!, values[0]!);
};
const subjects = computed(() => {
  const result = [...sourceSubjects.value];
  if (state.value.sort === "name") result.sort((a, b) => a.display_name.localeCompare(b.display_name));
  if (state.value.sort === "gap") result.sort((a, b) => compareValue(gap(b.target_id), gap(a.target_id)));
  return result;
});
const allExpanded = computed(() => subjects.value.length > 0 && subjects.value.every(subject => state.value.expanded.includes(subject.target_id)));
const metricLabel = computed(() => ({ questions: "Question score", cost: "Full round cost",
  duration: "Round duration", format: "Format errors" })[state.value.metric]);
const roundFormat = computed(() => roundMetricFormat(state.value.metric));

const update = (patch: LocationQueryRaw): void => {
  copied.value = "";
  shareUrl.value = "";
  void router.push({ name: "results-compare", params: { editionId: editionId.value },
    query: { ...route.query, comparisonNotice: undefined, ...patch } });
};
const modelIds = (items: readonly ComparisonModel[]) => items.map(model => model.result.model.model_id);
const add = (event: Event): void => {
  const picker = event.target as HTMLSelectElement;
  const id = picker.value; picker.value = "";
  if (selected.value.length < MAX_COMPARISON_MODELS &&
      available.value.some(model => model.result.model.model_id === id)) {
    update({ models: [...modelIds(selected.value), id].join(",") }); search.value = "";
    if (selected.value.length + 1 === MAX_COMPARISON_MODELS) pickerOpen.value = false;
  }
};
const remove = (id: string): void => {
  const remaining = modelIds(selected.value).filter(item => item !== id);
  update({ models: remaining.join(",") || undefined,
    baseline: state.value.baseline === id ? undefined : state.value.baseline || undefined });
};
const move = (index: number, direction: number): void => {
  const ids = modelIds(selected.value); const next = index + direction;
  if (next < 0 || next >= ids.length) return;
  [ids[index], ids[next]] = [ids[next]!, ids[index]!];
  update({ models: ids.join(",") });
};
const toggleSubject = (id: string): void => update({ expanded: (state.value.expanded.includes(id)
  ? state.value.expanded.filter(item => item !== id) : [...state.value.expanded, id]).join(",") || undefined });
const toggleAll = (): void => update({ expanded: allExpanded.value ? undefined : subjects.value.map(subject => subject.target_id).join(",") });
const change = (key: string, event: Event): void => {
  const value = (event.target as HTMLSelectElement).value;
  update({ [key]: value === "" || value === "questions" || value === "original" ? undefined : value });
};
const selectShareLink = (): void => {
  shareInput.value?.focus({ preventScroll: true });
  shareInput.value?.select();
};
const closeShare = (): void => {
  shareUrl.value = "";
  copied.value = "";
  shareButton.value?.focus({ preventScroll: true });
};
const share = async (): Promise<void> => {
  if (shareUrl.value) { closeShare(); return; }
  if (sharing.value) return;
  copied.value = "";
  if (typeof navigator.share === "function") {
    sharing.value = true;
    try {
      await navigator.share({ title: "Deep20Bench comparison", url: window.location.href });
      return;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
    } finally {
      sharing.value = false;
    }
  }
  shareUrl.value = window.location.href;
  await nextTick();
  selectShareLink();
};
const copyLink = async (): Promise<void> => {
  let success = false;
  if (typeof navigator.clipboard?.writeText === "function") {
    try { await navigator.clipboard.writeText(shareUrl.value); success = true; } catch { /* Try the selected-text fallback below. */ }
  }
  if (!success) {
    selectShareLink();
    // HTTP LAN previews cannot use the Clipboard API. Keep selection-based copying
    // as a best-effort fallback; manual selection remains available if it is denied.
    try { success = window.document.execCommand("copy"); } catch { /* Keep the link selected for manual copying. */ }
  }
  copied.value = success ? "Link copied." : "Could not copy automatically. Select the link and copy it.";
  if (success) copyButton.value?.focus({ preventScroll: true });
};
const referenceSubject = (id: string) => baseline.value === undefined ? null
  : subjectValue(subjectFor(baseline.value, id), state.value.metric);
const referenceRound = (id: string, number: number) => baseline.value === undefined ? null
  : roundValue(roundFor(baseline.value, id, number), state.value.metric);
const togglePicker = (event: Event): void => { pickerOpen.value = (event.target as HTMLDetailsElement).open; };
</script>

<template>
  <div class="page results-view compare-view">
    <section class="content-section">
      <div class="content-inner compare-content">
        <header class="compare-intro">
          <div>
            <h2>Compare models</h2>
            <p>Pick up to five models and see their results side by side.</p>
          </div>
          <button ref="shareButton" class="button button-primary" :disabled="selected.length === 0 || sharing"
            :aria-expanded="shareUrl ? true : undefined" :aria-controls="shareUrl ? 'comparison-share-panel' : undefined" @click="share">Share</button>
        </header>
        <div v-if="shareUrl" id="comparison-share-panel" class="compare-share-fallback" role="region" aria-label="Share comparison" @keydown.esc.stop.prevent="closeShare">
          <div class="compare-share-heading">
            <label for="comparison-share-link">Comparison link</label>
            <button class="button" @click="closeShare">Close</button>
          </div>
          <div class="compare-share-controls">
            <input id="comparison-share-link" ref="shareInput" :value="shareUrl" readonly @focus="shareInput?.select()" />
            <button ref="copyButton" class="button button-secondary" aria-label="Copy comparison link" @click="copyLink">{{ copied === 'Link copied.' ? 'Copied' : 'Copy' }}</button>
          </div>
        </div>
        <p class="compare-status" :class="{ 'has-message': copied }" role="status">{{ copied }}</p>
        <LoadingState v-if="loading && document === null" label="Loading comparison data" />
        <template v-else-if="error && document === null">
          <ErrorState :message="error" />
        </template>
        <template v-else-if="document !== null">
          <details class="compare-model-picker" :open="pickerOpen" @toggle="togglePicker">
            <summary><strong>Models</strong><span>{{ selected.length }} of {{ MAX_COMPARISON_MODELS }} selected</span><span aria-hidden="true">{{ pickerOpen ? '▾' : '▸' }}</span></summary>
            <div class="compare-picker">
            <label>Find a model
              <input v-model="search" type="search" placeholder="Name or provider" :disabled="selected.length >= MAX_COMPARISON_MODELS" />
            </label>
            <label>Add model
              <select aria-label="Add model" value="" :disabled="selected.length >= MAX_COMPARISON_MODELS" @change="add">
                <option value="">{{ selected.length >= MAX_COMPARISON_MODELS ? 'Remove a model to add another' : available.length === 0 ? 'No models match your search' : 'Choose a model…' }}</option>
                <option v-for="model in selected" :key="model.result.model.model_id" :value="model.result.model.model_id" disabled>{{ model.result.model.display_name }} - selected</option>
                <option v-for="model in available" :key="model.result.model.model_id" :value="model.result.model.model_id">{{ model.result.model.display_name }}</option>
              </select>
            </label>
            </div>
          <ul v-if="selected.length" class="compare-selections" aria-label="Selected models">
            <li v-for="(model, index) in selected" :key="model.result.model.model_id">
              <span><ModelName :name="model.result.model.display_name" compact /></span>
              <button v-if="selected.length > 1" :disabled="index === 0" :aria-label="`Move ${model.result.model.display_name} left`" @click="move(index, -1)">←</button>
              <button v-if="selected.length > 1" :disabled="index === selected.length - 1" :aria-label="`Move ${model.result.model.display_name} right`" @click="move(index, 1)">→</button>
              <button :aria-label="`Remove ${model.result.model.display_name}`" @click="remove(model.result.model.model_id)">×</button>
            </li>
          </ul>
          </details>
          <p v-if="missing.length || tooMany || (mounted && route.query.comparisonNotice)" class="compare-notice" role="status">
            <template v-if="missing.length">Not in this edition: {{ missing.join(', ') }}. </template>
            <template v-if="tooMany">Only the first five models are shown. </template>
            <template v-if="route.query.comparisonNotice">Some models are not in this edition and were removed.</template>
          </p>
          <p v-if="selected.length === 0" class="compare-empty">Add a model above to start.</p>
          <template v-else>
            <div class="compare-context">
              <p>Each model's latest ranked run: {{ document.target_ids.length }} subjects, {{ document.iterations }} rounds each.
                Shared links always show the latest results.</p>
              <label>Show differences from
                <select aria-label="Show differences from" :value="state.baseline" @change="change('baseline', $event)">
                  <option value="">None</option>
                  <option v-for="model in selected" :key="model.result.model.model_id" :value="model.result.model.model_id">{{ model.result.model.display_name }}</option>
                </select>
              </label>
            </div>
            <div class="compare-metric-heading">
              <h3>Main metrics</h3>
              <InfoPopover label="About metrics">
                <dl class="compare-metric-definitions">
                  <template v-for="metric in mainComparisonMetrics.filter(item => item.note)" :key="metric.key">
                    <dt>{{ metric.label }}</dt><dd>{{ metric.note }}</dd>
                  </template>
                </dl>
              </InfoPopover>
            </div>
            <p class="compare-help">Lower is better, except for rounds solved. Green marks the best value among these models, red the worst.</p>
            <p v-if="mainOverflow" class="compare-mobile-hint"><span aria-hidden="true">↔</span> Swipe to see more models</p>
            <ComparisonTable ref="mainScroll" :models="selectedNames" label="Main metric comparison" column-label="Metric" @overflow="mainOverflow = $event">
              <table class="compare-table compare-main-table">
                <caption class="visually-hidden">Main metrics for the selected models</caption>
                <thead><tr>
                  <th scope="col">Metric</th>
                  <th v-for="model in selected" :key="model.result.model.model_id" scope="col">
                    <div class="compare-model-heading">
                    <RouterLink class="compare-model-link" :to="modelSummaryRoute(model.result.model.model_id, model.result.execution_id!, editionId, detailQuery)"><ModelName :name="model.result.model.display_name" compact separated /></RouterLink>
                    <small class="compare-provider">{{ model.result.model.provider }}</small>
                    <small v-if="state.baseline" class="compare-reference" :aria-hidden="state.baseline !== model.result.model.model_id ? true : undefined">{{ state.baseline === model.result.model.model_id ? 'Reference' : '' }}</small>
                    <details class="compare-run"><summary>Run details</summary>
                      <RouterLink :to="runRoute(model.result.execution_id!, detailQuery)">{{ model.result.execution_id }}</RouterLink>
                      <PublicationTime v-if="model.result.completed_at" :value="model.result.completed_at" date-only />
                    </details>
                    </div>
                  </th>
                </tr></thead>
                <tbody><tr v-for="metric in mainComparisonMetrics" :key="metric.key" :data-metric="metric.key">
                  <th scope="row">{{ metric.label }}</th>
                  <td v-for="model in selected" :key="model.result.model.model_id" :data-state="valueMark(metric.value(model), selected.map(metric.value), metric.higherIsBetter)">
                    <ComparisonValue :value="metric.value(model)" :format="metric.format"
                      :mark="valueMark(metric.value(model), selected.map(metric.value), metric.higherIsBetter)"
                      :baseline="baseline && baseline !== model ? metric.value(baseline) : null">
                      <small v-if="metric.key === 'solved'">{{ model.result.successful }} of {{ model.result.terminal_trials }}</small>
                    </ComparisonValue>
                  </td>
                </tr></tbody>
              </table>
            </ComparisonTable>
            <p class="compare-help">Differences and colors describe the numbers only. They do not show whether a gap is statistically significant.</p>

            <header class="compare-round-heading">
              <div><h3>Subjects and rounds</h3><p>Select a subject to see its rounds. Each round links to its transcript.</p></div>
              <button class="button button-secondary" @click="toggleAll">{{ allExpanded ? 'Hide all rounds' : 'Show all rounds' }}</button>
            </header>
            <div class="compare-round-controls" role="group" aria-label="Subject and round display">
              <label>Metric<select aria-label="Metric" :value="state.metric" @change="change('metric', $event)">
                <option value="questions">Question score</option><option value="cost">Full round cost</option>
                <option value="duration">Round duration</option><option value="format">Format errors</option>
              </select></label>
              <label>Sort subjects<select aria-label="Sort subjects" :value="state.sort" @change="change('sort', $event)">
                <option value="original">Default order</option><option value="name">Name (A-Z)</option><option value="gap">Biggest gap first</option>
              </select></label>
            </div>
            <p class="compare-help">Lower is better. Subject rows show the average of their rounds.
              <template v-if="state.metric === 'questions'">A failed round scores {{ document.max_questions + 1 }}; if its counted questions differ, they appear below the score.</template>
              <template v-else-if="state.metric === 'cost'">Includes the tested model and the answer checks.</template>
              <template v-else-if="state.metric === 'duration'">Total time for the round, including answer checks.</template></p>
            <p v-if="subjectOverflow" class="compare-mobile-hint"><span aria-hidden="true">↔</span> Swipe to see more models</p>
            <ComparisonTable ref="subjectScroll" :models="selectedNames" label="Subject and round comparison" column-label="Subject / round" @overflow="subjectOverflow = $event">
              <table class="compare-table">
                <caption class="visually-hidden">{{ metricLabel }} by subject and round</caption>
                <thead><tr><th scope="col">Subject / round</th>
                  <th v-for="model in selected" :key="model.result.model.model_id" scope="col"><div class="compare-model-heading"><ModelName :name="model.result.model.display_name" compact separated /></div></th>
                </tr></thead>
                <tbody v-for="subject in subjects" :key="subject.target_id" :data-subject="subject.target_id" :data-expanded="state.expanded.includes(subject.target_id)">
                  <tr class="compare-subject-row" @click="toggleSubject(subject.target_id)">
                    <th scope="row"><button class="compare-expand" :aria-expanded="state.expanded.includes(subject.target_id)" :aria-label="`${state.expanded.includes(subject.target_id) ? 'Collapse' : 'Expand'} rounds for ${subject.display_name}`" @click.stop="toggleSubject(subject.target_id)">
                      <svg class="compare-chevron" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"><path d="m6 3 5 5-5 5" /></svg>
                      <span>{{ subject.display_name }}<small>Average</small></span>
                    </button></th>
                    <td v-for="model in selected" :key="model.result.model.model_id" class="compare-average-cell" :data-state="valueMark(subjectValue(subjectFor(model, subject.target_id), state.metric), subjectValues(subject.target_id))">
                      <div class="compare-average-value">
                      <ComparisonValue :value="subjectValue(subjectFor(model, subject.target_id), state.metric)" :format="roundFormat"
                        :mark="valueMark(subjectValue(subjectFor(model, subject.target_id), state.metric), subjectValues(subject.target_id))"
                        :baseline="baseline && baseline !== model ? referenceSubject(subject.target_id) : null">
                        <template v-if="state.expanded.includes(subject.target_id)" #leading>
                          <RouterLink class="compare-subject-link compare-detail-action" :to="subjectRoute(model.result.execution_id!, subject.target_id, detailQuery)" @click.stop>
                            <span class="visually-hidden">{{ model.result.model.display_name }}, {{ subject.display_name }}: </span>
                            <span class="compare-action-long">Open subject</span><span class="compare-action-short" aria-hidden="true">Subject</span> <span aria-hidden="true">→</span>
                          </RouterLink>
                        </template>
                      </ComparisonValue>
                      <span class="visually-hidden">{{ subjectFor(model, subject.target_id)?.successful }} of {{ document.iterations }} rounds solved.</span>
                      </div>
                    </td>
                  </tr>
                  <tr v-for="roundNumber in (state.expanded.includes(subject.target_id) ? rounds : [])" :key="roundNumber" class="compare-round-row" :data-round="roundNumber">
                    <th scope="row">Round {{ roundNumber }}</th>
                    <td v-for="model in selected" :key="model.result.model.model_id" class="compare-result-cell" :data-state="valueMark(roundValue(roundFor(model, subject.target_id, roundNumber), state.metric), roundValues(subject.target_id, roundNumber))">
                      <RouterLink v-if="roundFor(model, subject.target_id, roundNumber)" class="compare-result-link compare-round-link" :to="episodeRoute(model.result.execution_id!, subject.target_id, roundFor(model, subject.target_id, roundNumber)!.trial_id, detailQuery)">
                        <span class="visually-hidden">{{ model.result.model.display_name }}, {{ subject.display_name }}, round {{ roundNumber }}: </span>
                        <ComparisonValue :value="roundValue(roundFor(model, subject.target_id, roundNumber), state.metric)" :format="roundFormat" :digits="0"
                          :mark="valueMark(roundValue(roundFor(model, subject.target_id, roundNumber), state.metric), roundValues(subject.target_id, roundNumber))"
                          :baseline="baseline && baseline !== model ? referenceRound(subject.target_id, roundNumber) : null">
                          <template #leading><span class="compare-detail-action"><span class="compare-action-long">Open round</span><span class="compare-action-short" aria-hidden="true">Round</span> <span aria-hidden="true">→</span></span></template>
                        </ComparisonValue>
                        <span class="visually-hidden">{{ roundFor(model, subject.target_id, roundNumber)?.status === 'success' ? 'Solved.' : 'Not solved.' }}</span>
                        <span v-if="state.metric === 'questions' && countedQuestionsDiffer(model, subject.target_id, roundNumber)" class="compare-counted">{{ roundFor(model, subject.target_id, roundNumber)?.counted_questions }} counted</span>
                      </RouterLink>
                    </td>
                  </tr>
                </tbody>
              </table>
            </ComparisonTable>
            <p class="compare-help">Rounds line up by number for easier reading. They are not matched pairs.</p>
          </template>
          <noscript><p>Turn on JavaScript to choose models or open a shared link.</p></noscript>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.compare-content { min-width: 0; }
.compare-view :deep(.model-name) { align-items: baseline; }
.compare-view :deep(.model-name .model-name-effort) { padding: 0; border: 0; border-radius: 0; }
.compare-intro, .compare-round-heading { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.compare-intro h2, .compare-round-heading h3 { margin: 0; }
.compare-intro p, .compare-round-heading p { margin: 0.5rem 0 0; color: var(--text-secondary); }
.compare-status { margin: 0; font-size: 0.8125rem; }
.compare-status.has-message { margin-block: 0.75rem; }
.compare-share-fallback { margin-block: 0.75rem 1rem; padding: 0.75rem; border: var(--rule-default); background: var(--surface-raised); }
.compare-share-heading { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-bottom: 0.5rem; }
.compare-share-heading .button { padding-inline: 0.75rem; border-color: transparent; text-decoration: underline; text-underline-offset: 0.2em; }
.compare-share-controls { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.5rem; }
.compare-share-controls .button { min-width: 5rem; padding-inline: 0.75rem; }
.compare-picker, .compare-round-controls { display: flex; flex-wrap: wrap; align-items: end; gap: 1rem; }
.compare-picker { padding: 1rem; border: var(--rule-default); background: var(--surface-raised); }
.compare-model-picker { margin-block: 1.25rem 1rem; }
.compare-model-picker > summary { display: flex; gap: 0.75rem; align-items: center; min-height: 48px; padding: 0.6rem 1rem; border: var(--rule-default); background: var(--surface-raised); cursor: pointer; list-style: none; }
.compare-model-picker > summary::-webkit-details-marker { display: none; }
.compare-model-picker > summary > span:first-of-type { margin-left: auto; font-size: 0.8125rem; color: var(--text-secondary); }
.compare-model-picker[open] > summary { border-bottom: 0; }
.compare-model-picker[open] .compare-picker { border-top: 0; }
.compare-picker label { flex: 1 1 15rem; }
.compare-view label { display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.8125rem; font-weight: 600; min-width: 0; }
.compare-view input, .compare-view select { width: 100%; min-width: 0; min-height: 44px; height: 44px; border: var(--rule-default); border-radius: 4px; padding: 0.65rem; background: var(--paper-bright); color: var(--ink); font: inherit; font-size: 1rem; }
.compare-selections { display: flex; flex-wrap: wrap; gap: 0.65rem; list-style: none; padding: 0; margin: 1rem 0; }
.compare-selections li { display: flex; align-items: center; gap: 0.15rem; min-width: 0; max-width: 100%; padding-left: 0.75rem; border: var(--rule-default); background: var(--surface-accent-soft); }
.compare-selections li > span { padding-block: 0.5rem; min-width: 0; overflow-wrap: anywhere; }
.compare-selections button { flex: 0 0 44px; min-width: 44px; min-height: 44px; border: 0; background: transparent; color: var(--blue-ink); font-size: 1.1rem; cursor: pointer; }
.compare-selections button:disabled { color: var(--text-secondary); opacity: 0.4; cursor: default; }
.compare-notice { padding: 0.75rem; background: var(--surface-warning-soft); }
.compare-empty { padding: 2rem 1rem; border: var(--rule-default); text-align: center; color: var(--text-secondary); }
.compare-context { display: flex; align-items: end; justify-content: space-between; gap: 1.5rem; margin: 1.5rem 0; }
.compare-context p { max-width: 43rem; color: var(--text-secondary); font-size: 0.875rem; }
.compare-context label { flex: 0 1 20rem; }
.compare-help, .compare-mobile-hint { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.6; }
.compare-mobile-hint { display: none; }
.compare-metric-heading { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-top: 1.25rem; }
.compare-metric-heading h3 { margin: 0; }
.compare-metric-definitions { margin: 0; }
.compare-metric-definitions dt { color: var(--ink); font-weight: 600; }
.compare-metric-definitions dd { margin: 0.25rem 0 1rem; }
.compare-metric-definitions dd:last-child { margin-bottom: 0; }
.compare-table small { display: block; margin-top: 0.25rem; color: var(--text-secondary); font-size: 0.75rem; font-weight: 400; line-height: 1.4; }
.compare-table td { text-align: right; background: var(--surface-raised); }
.compare-main-table tbody th, .compare-main-table tbody td { padding: 0.65rem 1rem; vertical-align: middle; }
.compare-table td[data-state="best"] { background: var(--surface-success-soft); }
.compare-table td[data-state="worst"] { background: var(--surface-danger-soft); }
.compare-table th a { color: var(--ink); }
.compare-model-link { display: block; text-decoration: none; }
.compare-reference { min-height: 1.4em; }
.compare-run { margin-top: 0.5rem; font-size: 0.75rem; font-weight: 400; }
.compare-run summary { cursor: pointer; min-height: 44px; display: flex; justify-content: flex-end; align-items: center; text-decoration: underline; }
.compare-run summary::before { content: '▸'; margin-right: 0.25rem; }
.compare-run[open] summary::before { content: '▾'; }
.compare-run a, .compare-run time { display: block; margin-block: 0.5rem; }
.compare-round-heading { margin-top: 2.5rem; }
.compare-round-controls { margin-top: 1rem; padding: 0.875rem 1rem; border: var(--rule-default); background: var(--surface-raised); }
.compare-round-controls label { flex: 0 1 18rem; }
.compare-subject-row th, .compare-subject-row td { border-top: var(--rule-default); }
.compare-table tbody:first-of-type .compare-subject-row > * { border-top: 0; }
.compare-table tbody[data-expanded="true"] .compare-subject-row > th { background: var(--surface-accent-soft); }
.compare-subject-row th { vertical-align: middle; }
.compare-subject-row { cursor: pointer; }
.compare-table .compare-average-cell { position: relative; padding: 0; vertical-align: middle; }
.compare-average-value { min-height: 44px; padding: 0.65rem 1rem; }
.compare-subject-row:is(:hover, :focus-within) > :is(th, td)::after { content: ''; position: absolute; inset: 0; pointer-events: none; background: color-mix(in srgb, var(--blue-ink) 4%, transparent); }
.compare-table tbody[data-expanded="true"] .compare-round-row > th { background: var(--surface-accent-soft); border-inline-start: 3px solid var(--blue); }
.compare-detail-action { color: var(--blue-ink); font-size: 0.75rem; font-weight: 500; text-decoration: underline; text-underline-offset: 0.2em; white-space: nowrap; }
.compare-action-short { display: none; }
.compare-average-value, .compare-result-link { container: comparison-cell / inline-size; }
.compare-round-row:last-child > * { border-bottom: 2px solid var(--border-default); }
.compare-expand { display: flex; gap: 0.5rem; align-items: center; min-height: 44px; width: 100%; padding: 0; border: 0; background: transparent; color: var(--ink); font: inherit; font-weight: 600; text-align: left; cursor: pointer; }
.compare-chevron { flex: 0 0 16px; color: var(--blue-ink); fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; transition: transform 140ms ease; }
.compare-expand[aria-expanded="true"] .compare-chevron { transform: rotate(90deg); }
.compare-round-row th { padding-left: 2.25rem; vertical-align: middle; color: var(--text-secondary); font-weight: 400; }
.compare-table .compare-result-cell { position: relative; padding: 0; vertical-align: middle; }
.compare-result-link { display: flex; flex-direction: column; justify-content: center; gap: 0.35rem; min-height: 44px; height: 100%; padding: 0.65rem 1rem; color: inherit; text-decoration: none; }
.compare-result-link::after { content: ''; position: absolute; inset: 0; }
.compare-subject-link { display: inline-flex; align-items: center; gap: 0.2rem; min-height: 44px; }
.compare-round-row :deep(.comparison-value strong) { font-weight: 400; }
.compare-result-link:hover::after, .compare-result-link:focus-visible::after { background: color-mix(in srgb, var(--blue-ink) 4%, transparent); }
.compare-result-link:focus-visible { outline: none; }
.compare-result-link:focus-visible::after { outline: var(--focus-ring); outline-offset: -3px; }
.compare-counted { align-self: flex-end; color: var(--text-secondary); font-size: 0.75rem; line-height: 1.4; white-space: nowrap; }
.compare-view .button:disabled { opacity: 0.5; cursor: default; }
@media (max-width: 760px) {
  .compare-round-heading, .compare-context { align-items: stretch; flex-direction: column; }
  .compare-intro { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.75rem; }
  .compare-intro > div { display: contents; }
  .compare-intro h2 { font-size: 1.25rem; }
  .compare-intro p { grid-column: 1 / -1; grid-row: 2; margin: 0; }
  .compare-intro .button { grid-column: 2; grid-row: 1; padding-inline: 0.75rem; font-size: 0.8125rem; }
  .compare-picker { padding: 0.75rem; gap: 0.75rem; }
  .compare-picker label { flex-basis: 100%; }
  .compare-context { gap: 0.5rem; margin-block: 0.75rem; }
  .compare-context label { flex-basis: auto; }
  .compare-main-table tbody th, .compare-main-table tbody td { padding: 0.5rem 0.65rem; }
  .compare-round-row th { padding-left: 1.5rem; }
  .compare-round-controls label { flex: 1 1 100%; }
  .compare-round-controls { gap: 0.75rem; padding: 0.75rem; }
  .compare-result-link, .compare-average-value { padding: 0.65rem; }
  .compare-mobile-hint { display: block; }
  .compare-selections li { width: 100%; }
  .compare-selections li > span { flex: 1 1 auto; }
}
@container comparison (max-width: 600px) {
  .compare-main-table tbody th, .compare-main-table tbody td, .compare-average-value, .compare-result-link { padding: 0.5rem 0.375rem; }
  .compare-main-table tbody th { font-size: 0.75rem; }
  .compare-expand { gap: 0.375rem; }
  .compare-round-row th { padding-inline-start: 1.25rem; }
}
@container comparison-cell (max-width: 130px) {
  .compare-action-long { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .compare-action-short { display: inline; }
}
</style>
