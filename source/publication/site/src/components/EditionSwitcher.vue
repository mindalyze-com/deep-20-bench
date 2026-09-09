<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import EditionSummary from "@/components/EditionSummary.vue";
import { pendingEditionId } from "@/lib/api";
import { editionDestination, useEditionContext } from "@/lib/use-edition-context";

const route = useRoute();
const { editionId, editionsIndex, selectedEdition: selected, isPreviousEdition } = useEditionContext();
const picker = ref<HTMLDetailsElement | null>(null);
const trigger = ref<HTMLElement | null>(null);
const previewEditionId = ref<string | null>(null);
const previewEdition = (event: PointerEvent, editionId: string): void => {
  if (event.pointerType === "mouse") previewEditionId.value = editionId;
};
const previewFocusedEdition = (event: FocusEvent, editionId: string): void => {
  if (event.target instanceof Element && event.target.matches(":focus-visible")) {
    previewEditionId.value = editionId;
  }
};
const resetPreview = (): void => { previewEditionId.value = null; };
const handleToggle = (): void => {
  if (!picker.value?.open) resetPreview();
};
const notices: Record<string, string> = {
  "missing-model": "This model has no complete result in the selected edition. Showing its results overview.",
  "missing-subject": "This subject is not in the selected edition. Showing the model's run.",
  "episode-scope": "Rounds from different editions are separate games. Showing the subject's results.",
};
const notice = computed(() => typeof route.query.editionNotice === "string"
  ? notices[route.query.editionNotice] : undefined);
const pendingLabel = computed(() => editionsIndex.value?.editions.find(
  edition => edition.edition_id === pendingEditionId.value,
)?.label);
const closePicker = (): void => {
  resetPreview();
  if (picker.value !== null) picker.value.open = false;
};
const handleEscape = (event: KeyboardEvent): void => {
  if (!picker.value?.open) return;
  event.preventDefault();
  closePicker();
  trigger.value?.focus();
};
const closeOutside = (event: Event): void => {
  if (event.target instanceof Node && !picker.value?.contains(event.target)) closePicker();
};
const handleLink = (event: MouseEvent): void => {
  if (pendingEditionId.value !== null) event.preventDefault();
  else {
    closePicker();
    trigger.value?.focus({ preventScroll: true });
  }
};
watch(() => route.fullPath, closePicker);
onMounted(() => {
  document.addEventListener("pointerdown", closeOutside);
  document.addEventListener("focusin", closeOutside);
});
onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", closeOutside);
  document.removeEventListener("focusin", closeOutside);
});
</script>

<template>
  <div v-if="editionsIndex !== null" class="edition-bar site-boundary-shell">
    <div class="edition-bar-inner site-boundary">
      <details ref="picker" class="edition-picker" @keydown.esc="handleEscape" @toggle="handleToggle">
        <summary ref="trigger" class="edition-trigger" title="Change benchmark edition"
          :class="{ 'is-previous': isPreviousEdition }"
          :aria-label="`Benchmark edition: v.${editionId}, ${selected?.status === 'current' ? 'Current' : 'Previous'}`">
          <span class="edition-indicator" :class="{ 'is-current': selected?.status === 'current' }" aria-hidden="true"></span>
          <strong>v.{{ editionId }}</strong>
          <span class="edition-trigger-status">{{ selected?.status === 'current' ? 'Current' : 'Previous' }}</span>
          <svg class="edition-chevron" aria-hidden="true" width="12" height="8" viewBox="0 0 12 8"><path d="m1 1 5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.5" /></svg>
        </summary>
        <div class="edition-panel" @pointerleave="resetPreview">
          <p class="edition-panel-label">Benchmark edition</p>
          <nav class="edition-links" aria-label="Benchmark edition">
            <RouterLink v-for="edition in editionsIndex.editions" :key="edition.edition_id"
              :to="editionDestination(route, edition)"
              :aria-current="editionId === edition.edition_id ? 'true' : undefined"
              :class="{ 'is-previous': edition.status === 'previous' }"
              @pointerenter="previewEdition($event, edition.edition_id)"
              @focus="previewFocusedEdition($event, edition.edition_id)"
              :aria-disabled="pendingEditionId !== null ? 'true' : undefined" @click.capture="handleLink">
              <strong>v.{{ edition.edition_id }}</strong>
              <span class="edition-option-status" :class="{ 'is-current': edition.status === 'current' }">{{ edition.status === 'current' ? 'Current' : 'Previous edition' }}</span>
              <svg v-if="editionId === edition.edition_id" class="edition-check" aria-hidden="true" width="16" height="16" viewBox="0 0 16 16"><path d="m3 8 3 3 7-7" fill="none" stroke="currentColor" stroke-width="1.7" /></svg>
            </RouterLink>
          </nav>
          <EditionSummary :edition-id="previewEditionId ?? editionId" @navigate="closePicker" />
        </div>
      </details>
      <span class="edition-context" :class="{ 'is-loading': pendingEditionId !== null }" role="status">
        {{ pendingEditionId === null ? '' : `Loading edition ${pendingLabel}…` }}
      </span>
    </div>
    <p v-if="notice" class="edition-notice site-boundary" role="status">{{ notice }}</p>
  </div>
</template>

<style scoped>
.edition-bar { display: contents; }
.edition-bar-inner { display: flex; position: relative; grid-column: 2; grid-row: 1; align-items: center; width: auto; margin: 0; padding: 0; }
.edition-notice { font-size: var(--text-caption); color: var(--text-inverse-muted); }
.edition-picker { position: relative; }
.edition-trigger { display: flex; align-items: center; gap: .5rem; min-height: 44px; padding: .4rem .65rem; border: 0; border-radius: 7px; background: rgb(255 255 255 / 3%); color: var(--text-inverse); font-size: var(--text-ui); line-height: 1.4; list-style: none; cursor: pointer; }
.edition-trigger::-webkit-details-marker { display: none; }
.edition-trigger:hover, .edition-picker[open] .edition-trigger { background: rgb(255 255 255 / 6%); }
.edition-trigger:focus-visible { outline-color: var(--acid); }
.edition-trigger-status { color: var(--text-inverse-muted); font-size: var(--text-caption); }
.edition-indicator { width: 6px; height: 6px; border-radius: 50%; background: var(--text-inverse-muted); }
.edition-indicator.is-current { background: var(--acid); }
.edition-trigger.is-previous .edition-indicator { background: var(--state-warning); }
.edition-chevron { margin-left: .25rem; transition: transform 140ms ease; }
.edition-picker[open] .edition-chevron { transform: rotate(180deg); }
.edition-panel {
  color-scheme: dark;
  --text-primary: var(--text-inverse);
  --text-secondary: var(--text-inverse-muted);
  --surface-raised: var(--surface-inverse);
  --surface-rail: rgb(255 255 255 / 7%);
  --surface-success-soft: rgb(214 255 38 / 9%);
  --surface-danger-soft: rgb(233 90 61 / 12%);
  --state-clean-ink: var(--acid);
  --state-danger-ink: #ffad99;
  --blue-ink: #b3c5ff;
  --rule-default: var(--rule-inverse);
  --rule-subtle: var(--rule-inverse-subtle);
  --focus-ring: 3px solid var(--acid);
  position: absolute; z-index: 90; top: calc(100% + .5rem); right: 0;
  width: min(23rem, calc(100vw - 2 * var(--gutter))); max-height: calc(100dvh - 9rem);
  overflow-y: auto; overscroll-behavior: contain; padding: .65rem;
  border: var(--rule-default); border-radius: 12px; background: var(--surface-raised);
  color: var(--text-primary); box-shadow: 0 18px 48px rgb(0 0 0 / 35%);
}
.edition-panel-label { margin: .35rem .65rem .7rem; color: var(--text-primary); font-size: var(--text-caption); font-weight: var(--font-weight-semibold); }
.edition-links { display: grid; gap: .25rem; }
.edition-links a { display: flex; align-items: center; gap: .65rem; min-height: 52px; padding: .65rem .75rem; border: 1px solid transparent; border-radius: 7px; color: var(--text-primary); font-size: var(--text-ui); text-decoration: none; }
.edition-option-status { color: var(--text-secondary); font-size: var(--text-caption); }
.edition-option-status.is-current { padding: .1rem .4rem; border: 1px solid rgb(214 255 38 / 30%); border-radius: 5px; background: var(--surface-success-soft); color: var(--acid); font-size: var(--text-micro); font-weight: var(--font-weight-semibold); }
.edition-links a:hover { background: var(--surface-rail); }
.edition-links a[aria-current] { background: var(--surface-rail); border-color: var(--border-inverse-subtle); }
.edition-links a:focus-visible { outline: var(--focus-ring); outline-offset: -2px; }
.edition-links a[aria-disabled] { opacity: .6; cursor: progress; }
.edition-check { flex-shrink: 0; margin-left: auto; color: var(--acid); }
.edition-context { display: none; }
.edition-context.is-loading { display: block; position: absolute; z-index: 95; top: calc(100% + .35rem); right: 0; width: max-content; margin: 0; padding: .4rem .6rem; border: var(--rule-inverse); border-radius: 4px; background: var(--ink); color: var(--acid); font-size: var(--text-caption); }
.edition-notice { grid-column: 1 / -1; margin: 0; padding: .5rem 0; width: 100%; border-top: var(--rule-inverse); }
@media (max-width: 959px) {
  .edition-bar-inner, .edition-picker { position: static; }
  .edition-panel, .edition-context.is-loading { right: var(--gutter); }
  .edition-panel { max-height: calc(100dvh - 5rem); }
}
@media (max-width: 760px) {
  .edition-trigger { gap: .35rem; padding-inline: .4rem; }
  .edition-trigger-status { display: none; }
}
@media (min-width: 960px) {
  .edition-bar-inner { grid-column: 3; }
}
</style>
