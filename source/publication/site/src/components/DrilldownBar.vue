<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { routeContext } from "@/lib/route-context";

const route = useRoute();
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
      <div class="drilldown-label">
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
      <nav class="drilldown-mobile-crumbs" aria-label="Current location">
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
