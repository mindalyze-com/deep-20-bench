<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { comparisonReturnPath, isComparisonDetail } from "@/lib/comparison-navigation";

import { routeContext } from "@/lib/route-context";

const route = useRoute();
const router = useRouter();
const comparisonReturn = computed(() => isComparisonDetail(route.name)
  ? comparisonReturnPath(router, route.query) : null);
const level = computed(() => {
  if (routeContext.level) return routeContext.level;
  return typeof route.meta.context === "string" ? route.meta.context : "Publication";
});
const crumbs = computed(() => {
  if (routeContext.crumbs.length > 0) return routeContext.crumbs;
  const label =
    typeof route.meta.title === "string" ? route.meta.title : "Deep20Bench";
  return [{ label }];
});
const mobileCrumbs = computed(() => crumbs.value.slice(-2));
</script>

<template>
  <div class="drilldown-bar" :data-drilldown-level="level">
    <div class="drilldown-inner">
      <RouterLink v-if="comparisonReturn" class="comparison-return" :to="comparisonReturn">
        <span aria-hidden="true">←</span> Back to comparison
      </RouterLink>
      <div v-else class="drilldown-label">
        <span>{{ level }}</span>
        <strong v-if="routeContext.position">{{ routeContext.position }}</strong>
      </div>
      <nav class="drilldown-desktop-crumbs" aria-label="Current location">
        <template v-for="(crumb, index) in crumbs" :key="`${crumb.label}-${index}`">
          <span v-if="index > 0" class="crumb-separator" aria-hidden="true">/</span>
          <RouterLink v-if="crumb.to" :to="crumb.to">{{ crumb.label }}</RouterLink>
          <span v-else aria-current="page">{{ crumb.label }}</span>
        </template>
      </nav>
      <nav v-if="!comparisonReturn" class="drilldown-mobile-crumbs" aria-label="Current location">
        <template
          v-for="(crumb, index) in mobileCrumbs"
          :key="`mobile-${crumb.label}-${index}`"
        >
          <span v-if="index > 0" class="crumb-separator" aria-hidden="true">/</span>
          <RouterLink v-if="crumb.to" :to="crumb.to">
            <span v-if="index === 0" aria-hidden="true">←</span>
            {{ crumb.label }}
          </RouterLink>
          <span v-else aria-current="page">{{ crumb.label }}</span>
        </template>
      </nav>
      <div
        v-if="routeContext.previous || routeContext.next"
        class="sibling-controls"
        aria-label="Sibling navigation"
      >
        <RouterLink
          v-if="routeContext.previous"
          :to="routeContext.previous.to"
          rel="prev"
          :aria-label="`Previous: ${routeContext.previous.label}`"
        >
          <span aria-hidden="true">←</span><span>{{ routeContext.previous.label }}</span>
        </RouterLink>
        <span v-else aria-hidden="true"></span>
        <RouterLink
          v-if="routeContext.next"
          :to="routeContext.next.to"
          rel="next"
          :aria-label="`Next: ${routeContext.next.label}`"
        >
          <span>{{ routeContext.next.label }}</span><span aria-hidden="true">→</span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comparison-return { display: inline-flex; align-items: center; gap: 0.4rem; min-width: 0; min-height: 44px; color: var(--blue-ink); font-size: var(--text-small); font-weight: 600; text-decoration: none; white-space: nowrap; }
.comparison-return:hover { text-decoration: underline; text-underline-offset: 0.2em; }
</style>
