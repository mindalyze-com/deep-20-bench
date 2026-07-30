<script setup lang="ts">
const links = [
  { label: "Overview", name: "results" },
  { label: "Cost", name: "results-cost" },
  { label: "Time", name: "results-time" },
  { label: "Efficiency", name: "results-efficiency" },
] as const;
</script>

<template>
  <nav class="results-nav" aria-label="Result views">
    <RouterLink
      v-for="link in links"
      :key="link.name"
      :to="{ name: link.name }"
      exact-active-class="active"
    >
      {{ link.label }}
    </RouterLink>
  </nav>
</template>

<style scoped>
.results-nav {
  display: flex;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding-inline: var(--gutter);
  border-bottom: 1px solid var(--line);
  background: var(--paper-bright);
  scrollbar-width: thin;
}

a {
  position: relative;
  flex: 0 0 auto;
  min-height: 44px;
  padding: 1.05rem clamp(0.75rem, 2vw, 1.5rem);
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 720;
  text-decoration: none;
}

a.active {
  color: var(--ink);
}

a.active::after {
  position: absolute;
  right: 0.75rem;
  bottom: -1px;
  left: 0.75rem;
  height: 3px;
  background: var(--blue);
  content: "";
}
</style>
