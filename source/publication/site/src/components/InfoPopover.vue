<script setup lang="ts">
import {
  onBeforeUnmount,
  onDeactivated,
  ref,
  useId,
} from "vue";

const props = withDefaults(
  defineProps<{
    label: string;
    align?: "start" | "end";
  }>(),
  {
    align: "end",
  },
);

const open = ref(false);
const positioned = ref(false);
const panel = ref<HTMLElement | null>(null);
const trigger = ref<HTMLButtonElement | null>(null);
const instanceId = useId();
const panelId = `info-popover-panel-${instanceId}`;
const titleId = `info-popover-title-${instanceId}`;
let frame = 0;
let observer: ResizeObserver | null = null;

const close = (restoreFocus = false): void => {
  if (panel.value?.matches(":popover-open")) panel.value.hidePopover();
  if (restoreFocus) trigger.value?.focus({ preventScroll: true });
};

const positionPanel = (): void => {
  frame = 0;
  const element = panel.value;
  const button = trigger.value;
  if (!open.value || element === null || button === null) return;
  const viewport = window.visualViewport;
  const leftEdge = (viewport?.offsetLeft ?? 0) + 12;
  const topEdge = (viewport?.offsetTop ?? 0) + 12;
  const rightEdge = leftEdge + (viewport?.width ?? document.documentElement.clientWidth) - 24;
  const bottomEdge = topEdge + (viewport?.height ?? window.innerHeight) - 24;
  const anchor = button.getBoundingClientRect();
  if (anchor.bottom <= topEdge - 12 || anchor.top >= bottomEdge + 12 ||
      anchor.right <= leftEdge - 12 || anchor.left >= rightEdge + 12) { close(); return; }

  element.style.maxWidth = `${Math.max(0, rightEdge - leftEdge)}px`;
  const width = element.getBoundingClientRect().width;
  const header = element.querySelector("header")!;
  const body = element.querySelector<HTMLElement>(".info-popover-body")!;
  const naturalHeight = header.getBoundingClientRect().height + body.scrollHeight + element.offsetHeight - element.clientHeight;
  const belowSpace = Math.max(0, bottomEdge - anchor.bottom - 8);
  const aboveSpace = Math.max(0, anchor.top - topEdge - 8);
  const below = naturalHeight <= belowSpace || belowSpace >= aboveSpace;
  const space = below ? belowSpace : aboveSpace;
  const adjacent = space >= 144;
  const maxHeight = adjacent ? space : bottomEdge - topEdge;
  const height = Math.min(naturalHeight, maxHeight);
  const left = Math.max(leftEdge, Math.min(props.align === "start" ? anchor.left : anchor.right - width, rightEdge - width));
  const desiredTop = below ? anchor.bottom + 8 : anchor.top - height - 8;
  const top = Math.max(topEdge, Math.min(desiredTop, bottomEdge - height));
  element.style.left = `${left}px`;
  element.style.top = `${top}px`;
  element.style.maxHeight = `${maxHeight}px`;
  element.style.setProperty("--popover-anchor-x", `${Math.max(16, Math.min((anchor.left + anchor.right) / 2 - left, width - 16))}px`);
  element.dataset.placement = adjacent ? (below ? "below" : "above") : "overlay";
  element.style.visibility = "visible";
  positioned.value = true;
};

const schedulePosition = (): void => {
  if (frame === 0) frame = window.requestAnimationFrame(positionPanel);
};
const handleKeyDown = (event: KeyboardEvent): void => {
  if (event.key !== "Escape") return;
  event.preventDefault();
  event.stopPropagation();
  close(true);
};
const stopTracking = (): void => {
  window.cancelAnimationFrame(frame);
  frame = 0;
  observer?.disconnect();
  observer = null;
  window.removeEventListener("scroll", schedulePosition, true);
  window.removeEventListener("resize", schedulePosition);
  window.removeEventListener("keydown", handleKeyDown);
  window.visualViewport?.removeEventListener("scroll", schedulePosition);
  window.visualViewport?.removeEventListener("resize", schedulePosition);
};
const handleBeforeToggle = (event: Event): void => {
  open.value = (event as ToggleEvent).newState === "open";
  positioned.value = false;
  if (panel.value) panel.value.style.visibility = "hidden";
  stopTracking();
  if (!open.value) return;
  trigger.value?.focus({ preventScroll: true });
  window.addEventListener("scroll", schedulePosition, { capture: true, passive: true });
  window.addEventListener("resize", schedulePosition, { passive: true });
  window.addEventListener("keydown", handleKeyDown);
  window.visualViewport?.addEventListener("scroll", schedulePosition, { passive: true });
  window.visualViewport?.addEventListener("resize", schedulePosition, { passive: true });
  observer = new ResizeObserver(schedulePosition);
  if (panel.value) observer.observe(panel.value);
  if (trigger.value) observer.observe(trigger.value);
  schedulePosition();
};
onDeactivated(() => close());
onBeforeUnmount(() => {
  close();
  stopTracking();
});
</script>

<template>
  <div
    class="info-popover"
    :class="[`info-popover--${align}`, { 'info-popover--open': open }]"
  >
    <button
      ref="trigger"
      class="info-popover-trigger"
      type="button"
      :aria-expanded="open"
      :aria-controls="panelId"
      aria-haspopup="dialog"
      :popovertarget="panelId"
    >
      <span class="info-popover-indicator" aria-hidden="true">i</span>
      <slot name="trigger">{{ label }}</slot>
    </button>

      <section
        ref="panel"
        :id="panelId"
        class="info-popover-panel"
        :class="{ 'info-popover-panel--positioned': positioned }"
        popover="auto"
        role="dialog"
        :aria-labelledby="titleId"
        @beforetoggle="handleBeforeToggle"
      >
        <header>
          <strong :id="titleId">{{ label }}</strong>
          <button
            type="button"
            aria-label="Close explanation"
            @click="close(true)"
          >
            <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false"><path d="m5 5 10 10M15 5 5 15" /></svg>
          </button>
        </header>
        <div class="info-popover-body">
          <slot />
        </div>
      </section>
  </div>
</template>

<style scoped>
.info-popover {
  position: relative;
  width: fit-content;
  max-width: 100%;
}

.info-popover-trigger {
  display: inline-flex;
  gap: 0.4rem;
  align-items: center;
  width: fit-content;
  min-height: 44px;
  padding: 0.45rem 0;
  border: 0;
  background: transparent;
  color: inherit;
  font-size: var(--text-small);
  font-weight: var(--font-weight-bold);
  line-height: 1.35;
  text-align: left;
  cursor: pointer;
}

.info-popover-trigger:hover {
  text-decoration: underline;
  text-underline-offset: 0.24em;
}

.info-popover-indicator {
  display: grid;
  place-items: center;
  width: 1rem;
  height: 1rem;
  border: var(--border-width) solid currentColor;
  border-radius: 50%;
  font: var(--font-weight-bold) 0.62rem/1 var(--font-sans);
  background: color-mix(in srgb, currentColor 8%, transparent);
  opacity: 1;
}

.info-popover-trigger:hover .info-popover-indicator,
.info-popover-trigger:focus-visible .info-popover-indicator,
.info-popover--open .info-popover-indicator {
  background: color-mix(in srgb, currentColor 16%, transparent);
}

.info-popover-panel {
  position: fixed;
  z-index: 120;
  inset: auto;
  width: 22rem;
  max-width: calc(100vw - 1.5rem);
  margin: 0;
  padding: 0;
  border: var(--rule-default);
  border-radius: 0.75rem;
  background: var(--paper-bright);
  box-shadow: 0 8px 28px rgb(17 19 28 / 14%);
  color: var(--ink);
  visibility: hidden;
  overflow: visible;
}
.info-popover-panel:popover-open {
  display: flex;
  flex-direction: column;
}
.info-popover-panel--positioned { visibility: visible; }
.info-popover-panel::before {
  content: '';
  position: absolute;
  left: var(--popover-anchor-x);
  width: 10px;
  height: 10px;
  background: var(--paper-bright);
  transform: translateX(-50%) rotate(45deg);
}
.info-popover-panel[data-placement="below"]::before {
  top: -6px;
  border-top: var(--rule-default);
  border-left: var(--rule-default);
}
.info-popover-panel[data-placement="above"]::before {
  bottom: -6px;
  border-bottom: var(--rule-default);
  border-right: var(--rule-default);
}
.info-popover-panel[data-placement="overlay"]::before { display: none; }

.info-popover-panel header {
  display: flex;
  flex: 0 0 auto;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: center;
  padding: 0.5rem 0.5rem 0.25rem 1rem;
}

.info-popover-panel header strong {
  min-width: 0;
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: 0;
  text-wrap: balance;
}

.info-popover-panel header button {
  display: grid;
  flex: 0 0 44px;
  place-items: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border: 0;
  border-radius: 0.5rem;
  background: transparent;
  color: var(--text-secondary);
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
}

.info-popover-panel header button:hover {
  background: var(--surface-raised);
  color: var(--ink);
}
.info-popover-panel header button svg { fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; }

.info-popover-body {
  min-height: 0;
  border-radius: 0 0 0.7rem 0.7rem;
  overflow-y: auto;
  overscroll-behavior: contain;
  overflow-wrap: anywhere;
  padding: 0.25rem 1rem 1rem;
  color: var(--text-secondary);
  font-size: var(--text-small);
  line-height: 1.6;
}
.info-popover-body :deep(p) { margin: 0; }
.info-popover-body :deep(p + p) { margin-top: 0.65rem; }

</style>
