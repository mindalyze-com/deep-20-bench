<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
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
</script>

<template>
  <header class="site-header">
    <RouterLink class="wordmark" :to="{ name: 'home' }" aria-label="Deep20Bench home">
      <span aria-hidden="true">D20</span>
      <span>Deep20Bench</span>
    </RouterLink>
    <nav aria-label="Primary navigation">
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
      <span>Source</span>
      <span aria-hidden="true">↗</span>
      <span class="visually-hidden">(opens in a new tab)</span>
    </a>
  </header>
</template>
