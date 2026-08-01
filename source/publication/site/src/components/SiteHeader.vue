<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const mobileNavigation = ref<HTMLDetailsElement | null>(null);
const links = [
  { label: "Overview", name: "home", glyph: "◉" },
  { label: "Results", name: "results", glyph: "▥" },
  { label: "Method", name: "methodology", glyph: "⌁" },
  { label: "Story", name: "story", glyph: "✦" },
  { label: "Data", name: "data", glyph: "↓" },
] as const;

const active = computed(() =>
  typeof route.meta.nav === "string" ? route.meta.nav : null,
);

const closeMobileNavigation = (): void => {
  if (mobileNavigation.value !== null) mobileNavigation.value.open = false;
};

watch(() => route.fullPath, closeMobileNavigation);
</script>

<template>
  <header class="site-header">
    <RouterLink class="wordmark" :to="{ name: 'home' }" aria-label="Deep20Bench home">
      <span aria-hidden="true">D20</span>
      <span>Deep20Bench</span>
    </RouterLink>
    <nav class="primary-navigation" aria-label="Primary navigation">
      <RouterLink
        v-for="link in links"
        :key="link.name"
        :to="{ name: link.name }"
        :aria-current="active === link.label ? 'page' : undefined"
      >
        <span class="nav-glyph" aria-hidden="true">{{ link.glyph }}</span>
        <span>{{ link.label }}</span>
      </RouterLink>
    </nav>
    <a
      class="repository-link"
      href="https://github.com/mindalyze-com/deep-20-bench"
      target="_blank"
      rel="noreferrer"
      aria-label="Source code (opens in a new tab)"
    >
      <svg
        class="repository-icon"
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path
          d="M12 .7a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2.23c-3.22.7-3.9-1.37-3.9-1.37-.52-1.34-1.28-1.7-1.28-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.18 1.77 1.18 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.57-.29-5.27-1.28-5.27-5.68 0-1.26.45-2.28 1.18-3.09-.12-.29-.51-1.47.11-3.05 0 0 .96-.31 3.16 1.18A10.94 10.94 0 0 1 12 6.11c.98 0 1.95.13 2.87.39 2.19-1.49 3.16-1.18 3.16-1.18.62 1.58.23 2.76.11 3.05.73.81 1.18 1.83 1.18 3.09 0 4.41-2.71 5.38-5.29 5.67.42.36.79 1.06.79 2.14v3.28c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .7Z"
        />
      </svg>
      <span class="repository-label">Source</span>
      <span aria-hidden="true">↗</span>
      <span class="visually-hidden">(opens in a new tab)</span>
    </a>
    <details
      ref="mobileNavigation"
      class="mobile-navigation"
      @keydown.esc="closeMobileNavigation"
    >
      <summary>
        <span class="mobile-navigation-glyph" aria-hidden="true">☰</span>
        <span>Menu</span>
      </summary>
      <nav aria-label="Mobile primary navigation">
        <RouterLink
          v-for="link in links"
          :key="`mobile-${link.name}`"
          :to="{ name: link.name }"
          :aria-current="active === link.label ? 'page' : undefined"
          @click="closeMobileNavigation"
        >
          <span class="nav-glyph" aria-hidden="true">{{ link.glyph }}</span>
          <span>{{ link.label }}</span>
        </RouterLink>
      </nav>
    </details>
  </header>
</template>
