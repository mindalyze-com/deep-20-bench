<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import ModelName from "@/components/ModelName.vue";

const props = defineProps<{ models: readonly string[]; label: string; columnLabel: string }>();
const emit = defineEmits<{ overflow: [value: boolean] }>();
const shell = ref<HTMLDivElement | null>(null);
const scroller = ref<HTMLDivElement | null>(null);
const headerScroller = ref<HTMLDivElement | null>(null);
const pinned = ref(false);
let frame = 0;
let observer: ResizeObserver | null = null;
let lastOverflow: boolean | null = null;
let headingsDirty = true;

const contentHeight = (element: Element | null): number => {
  if (element === null) return 0;
  const range = element.ownerDocument.createRange();
  range.selectNodeContents(element);
  return range.getBoundingClientRect().height;
};
const alignHeadings = (container: HTMLElement | null): void => {
  if (container === null) return;
  const names = [...container.querySelectorAll("thead .model-name")];
  const setHeight = (property: string, heights: number[]): void => {
    const height = `${Math.ceil(Math.max(0, ...heights))}px`;
    if (container.style.getPropertyValue(property) !== height) container.style.setProperty(property, height);
  };
  // Measure the text, rather than the reserved box, so headers can shrink again
  // when a long name is removed or the available column width increases.
  setHeight("--compare-label-height", names.map(name => contentHeight(name.querySelector(".model-name-label"))));
  setHeight("--compare-name-height", names.map(contentHeight));
};
const update = (): void => {
  frame = 0;
  if (headingsDirty) {
    alignHeadings(scroller.value);
    alignHeadings(headerScroller.value);
    headingsDirty = false;
  }
  const bounds = shell.value?.getBoundingClientRect();
  pinned.value = bounds !== undefined && bounds.top < 0 && bounds.bottom > 0;
  const overflowing = scroller.value !== null && scroller.value.scrollWidth > scroller.value.clientWidth + 1;
  if (overflowing !== lastOverflow) { lastOverflow = overflowing; emit("overflow", overflowing); }
};
const schedule = (): void => {
  if (frame === 0) frame = window.requestAnimationFrame(update);
};
const scheduleHeadings = (): void => { headingsDirty = true; schedule(); };
watch(() => props.models, scheduleHeadings, { flush: "post" });
const syncFromTable = (): void => {
  if (scroller.value && headerScroller.value) headerScroller.value.scrollLeft = scroller.value.scrollLeft;
};
const syncFromHeader = (): void => {
  if (scroller.value && headerScroller.value) scroller.value.scrollLeft = headerScroller.value.scrollLeft;
};

defineExpose({
  get scrollLeft(): number { return scroller.value?.scrollLeft ?? 0; },
  set scrollLeft(value: number) {
    if (scroller.value) scroller.value.scrollLeft = value;
    syncFromTable();
  },
});
onMounted(() => {
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", scheduleHeadings, { passive: true });
  observer = new ResizeObserver(() => { syncFromTable(); scheduleHeadings(); });
  if (shell.value) observer.observe(shell.value);
  const table = scroller.value?.querySelector("table");
  if (table) observer.observe(table);
  void document.fonts.ready.then(() => { if (shell.value) scheduleHeadings(); });
  update();
});
onBeforeUnmount(() => {
  window.removeEventListener("scroll", schedule);
  window.removeEventListener("resize", scheduleHeadings);
  window.cancelAnimationFrame(frame);
  observer?.disconnect();
});
</script>

<template>
  <div ref="shell" class="comparison-table-shell" :style="{ '--model-count': models.length }">
    <!-- A compact visual copy sits outside the horizontal scrollport, so the document
         remains the vertical scroll surface. The original table owns accessible headers. -->
    <div class="comparison-pinned-header" :class="{ 'is-pinned': pinned }" aria-hidden="true">
      <div ref="headerScroller" class="comparison-header-scroll" tabindex="-1" @scroll="syncFromHeader">
        <table class="compare-table">
          <thead><tr>
            <th>{{ columnLabel }}</th>
            <th v-for="(model, index) in models" :key="index"><div class="compare-model-heading"><ModelName :name="model" compact separated /></div></th>
          </tr></thead>
        </table>
      </div>
    </div>
    <div ref="scroller" class="compare-scroll" role="region" :aria-label="label" tabindex="0" @scroll="syncFromTable">
      <slot />
    </div>
  </div>
</template>

<style scoped>
/* Horizontal clipping must not create an ancestor scrollport for the sticky header. */
:global(html:has(.comparison-table-shell)), :global(body:has(.comparison-table-shell)), :global(#app:has(.comparison-table-shell)) { overflow-x: clip; overflow-y: visible; }
.comparison-table-shell { --label-width: 230px; --model-width: 210px; container: comparison / inline-size; display: grid; grid-template-columns: minmax(0, 1fr); min-width: 0; }
.comparison-table-shell :deep(.compare-model-heading) { container: comparison-model / inline-size; min-width: 0; }
.comparison-table-shell :deep(.model-name.separated) { min-height: var(--compare-name-height, 0px); justify-content: flex-end; align-content: flex-start; }
.compare-scroll, .comparison-pinned-header { grid-area: 1 / 1; min-width: 0; }
.compare-scroll { max-width: 100%; overflow-x: auto; overflow-y: hidden; border: var(--rule-default); isolation: isolate; }
.comparison-pinned-header { position: sticky; top: 0; align-self: start; z-index: 4; visibility: hidden; border: var(--rule-default); background: var(--paper-bright); box-shadow: var(--shadow-floating); }
.comparison-pinned-header.is-pinned { visibility: visible; }
.comparison-header-scroll { overflow-x: auto; scrollbar-width: none; }
.comparison-header-scroll::-webkit-scrollbar { display: none; }
.comparison-table-shell :deep(.compare-table) { width: 100%; min-width: calc(var(--label-width) + var(--model-width) * var(--model-count)); border-collapse: separate; border-spacing: 0; table-layout: fixed; font-size: 0.875rem; }
.comparison-table-shell :deep(:where(.compare-table th, .compare-table td)) { padding: 0.85rem 1rem; vertical-align: top; border-bottom: var(--rule-subtle); border-right: var(--rule-subtle); overflow-wrap: anywhere; }
.comparison-table-shell :deep(.compare-table tr > :first-child) { position: sticky; left: 0; z-index: 1; width: var(--label-width); background: var(--paper-bright); text-align: left; box-shadow: 1px 0 0 var(--line); }
.comparison-table-shell :deep(.compare-table thead th) { background: var(--paper-bright); text-align: right; }
.comparison-table-shell :deep(.compare-table thead th:first-child) { z-index: 3; }
.comparison-table-shell :deep(a), .comparison-table-shell :deep(button) { scroll-margin-top: 5rem; }
.comparison-pinned-header .compare-table th { padding-block: 0.5rem; vertical-align: middle; height: 44px; font-size: 0.8125rem; }
@media (max-width: 760px) {
  .comparison-table-shell { --label-width: 145px; --model-width: 175px; }
  .comparison-table-shell :deep(:where(.compare-table th, .compare-table td)) { padding: 0.65rem; }
  .comparison-pinned-header .compare-table th { padding-block: 0.5rem; }
}
@media (max-width: 380px) {
  .comparison-table-shell { --label-width: 120px; --model-width: 160px; }
}
@container comparison (max-width: 600px) {
  .compare-scroll, .comparison-pinned-header { --label-width: clamp(104px, 32cqw, 144px); --model-width: calc((100cqw - var(--label-width) - 2px) / 2); }
  .comparison-table-shell :deep(:where(.compare-table th, .compare-table td)) { padding: 0.5rem 0.375rem; }
  .comparison-table-shell :deep(.compare-table tr > :first-child) { font-size: 0.75rem; }
}
@container comparison-model (max-width: 260px) {
  .comparison-table-shell :deep(.model-name.separated) { flex-direction: column; flex-wrap: nowrap; align-items: center; justify-content: flex-start; gap: 0.2rem; }
  .comparison-table-shell :deep(.model-name.separated .model-name-label) { display: flex; flex-direction: column; align-items: center; align-self: stretch; min-height: var(--compare-label-height, 0px); text-align: center; line-height: 1.3; }
  .comparison-table-shell :deep(.model-name-family) { color: var(--text-secondary); font-size: 0.75rem; font-weight: 500; }
  .comparison-table-shell :deep(.model-name-variant) { font-size: 0.8125rem; font-weight: 600; }
  .comparison-table-shell :deep(.model-name.separated .model-name-effort) { font-size: 0.6875rem; font-weight: 400; }
  .comparison-table-shell :deep(.compare-provider) { display: none; }
  .comparison-table-shell :deep(.compare-reference) { text-align: center; }
  .comparison-table-shell :deep(.compare-run summary) { justify-content: center; }
}
@container comparison-model (max-width: 80px) {
  .comparison-table-shell :deep(.model-name-variant) { font-size: 0.75rem; }
}
</style>
