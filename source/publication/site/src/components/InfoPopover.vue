<script setup lang="ts">
import {
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  useId,
} from "vue";

withDefaults(
  defineProps<{
    label: string;
    align?: "start" | "end";
  }>(),
  {
    align: "end",
  },
);

const open = ref(false);
const root = ref<HTMLDivElement | null>(null);
const trigger = ref<HTMLButtonElement | null>(null);
const instanceId = useId();
const panelId = `info-popover-panel-${instanceId}`;
const titleId = `info-popover-title-${instanceId}`;

const close = (restoreFocus = false): void => {
  if (!open.value) return;
  open.value = false;
  if (restoreFocus) {
    void nextTick(() => trigger.value?.focus());
  }
};

const toggle = (): void => {
  open.value = !open.value;
};

const handlePointerDown = (event: PointerEvent): void => {
  const target = event.target;
  if (
    open.value &&
    target instanceof Node &&
    root.value !== null &&
    !root.value.contains(target)
  ) {
    close();
  }
};

const handleKeyDown = (event: KeyboardEvent): void => {
  if (open.value && event.key === "Escape") {
    event.preventDefault();
    close(true);
  }
};

onMounted(() => {
  document.addEventListener("pointerdown", handlePointerDown);
  document.addEventListener("keydown", handleKeyDown);
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", handlePointerDown);
  document.removeEventListener("keydown", handleKeyDown);
});
</script>

<template>
  <div
    ref="root"
    class="info-popover"
    :class="[`info-popover--${align}`, { 'info-popover--open': open }]"
  >
    <button
      ref="trigger"
      class="info-popover-trigger"
      type="button"
      :aria-expanded="open"
      :aria-controls="panelId"
      @click="toggle"
    >
      <span class="info-popover-indicator" aria-hidden="true">i</span>
      <slot name="trigger">{{ label }}</slot>
    </button>

    <Transition name="info-popover-panel">
      <section
        v-if="open"
        :id="panelId"
        class="info-popover-panel"
        role="dialog"
        :aria-labelledby="titleId"
      >
        <header>
          <strong :id="titleId">{{ label }}</strong>
          <button
            type="button"
            aria-label="Close explanation"
            @click="close(true)"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>
        <div class="info-popover-body">
          <slot />
        </div>
      </section>
    </Transition>
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
  font-weight: 720;
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
  font: 760 0.62rem/1 var(--font-sans);
  opacity: 0.72;
}

.info-popover-panel {
  position: absolute;
  z-index: 120;
  top: calc(100% + 0.55rem);
  width: min(22rem, calc(100vw - 2rem));
  border: var(--rule-default);
  background: var(--paper-bright);
  box-shadow: 0 18px 48px rgb(17 19 28 / 20%);
  color: var(--ink);
}

.info-popover--start .info-popover-panel {
  left: 0;
}

.info-popover--end .info-popover-panel {
  right: 0;
}

.info-popover-panel header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 0.8rem 0.9rem;
  border-bottom: var(--rule-subtle);
}

.info-popover-panel header strong {
  font-size: var(--text-small);
  letter-spacing: 0.02em;
}

.info-popover-panel header button {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border: var(--rule-default);
  background: transparent;
  color: var(--ink);
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
}

.info-popover-panel header button:hover {
  border-color: var(--ink);
}

.info-popover-body {
  padding: 0.9rem;
  color: var(--muted);
  font-size: var(--text-small);
  line-height: 1.6;
}

.info-popover-panel-enter-active,
.info-popover-panel-leave-active {
  transition:
    opacity 140ms ease,
    transform 140ms ease;
}

.info-popover-panel-enter-from,
.info-popover-panel-leave-to {
  opacity: 0;
  transform: translateY(-0.25rem);
}

@media (max-width: 620px) {
  .info-popover-panel {
    position: fixed;
    right: 1rem !important;
    bottom: calc(env(safe-area-inset-bottom) + 1rem);
    left: 1rem !important;
    top: auto;
    width: auto;
    max-height: min(22rem, calc(100dvh - 9rem));
    overflow-y: auto;
  }
}
</style>
