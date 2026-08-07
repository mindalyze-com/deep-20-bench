<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

const links = [
  { label: "Score", name: "results" },
  { label: "Stability", name: "results-reliability" },
  { label: "Cost", name: "results-cost" },
  { label: "Time", name: "results-time" },
  { label: "Efficiency", name: "results-efficiency" },
] as const;

const route = useRoute();
const navigation = ref<HTMLElement | null>(null);

const revealActiveLink = async (): Promise<void> => {
  await nextTick();
  navigation.value
    ?.querySelector<HTMLElement>("a.active")
    ?.scrollIntoView({ block: "nearest", inline: "nearest" });
};

onMounted(() => {
  void revealActiveLink();
});
watch(
  () => route.name,
  () => {
    void revealActiveLink();
  },
  { flush: "post" },
);
</script>

<template>
  <nav ref="navigation" class="results-nav" aria-label="Result views">
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
  border-bottom: var(--rule-default);
  background: var(--paper-bright);
  scrollbar-width: none;
}

.results-nav::-webkit-scrollbar {
  display: none;
}

a {
  position: relative;
  flex: 0 0 auto;
  min-height: 44px;
  padding: 1.05rem clamp(0.75rem, 2vw, 1.5rem);
  color: var(--muted);
  font-size: var(--text-ui);
  font-weight: var(--font-weight-bold);
  text-decoration: none;
}

a.active {
  color: var(--result-accent-ink, var(--ink));
}

a.active::after {
  position: absolute;
  right: 0.75rem;
  bottom: -1px;
  left: 0.75rem;
  height: 3px;
  background: var(--result-accent, var(--blue));
  content: "";
}
</style>
