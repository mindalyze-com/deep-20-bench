<script setup lang="ts">
import { onActivated } from "vue";

import { setRouteContext } from "@/lib/route-context";

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Page not found",
    description: "The requested Deep20Bench page is not in the current publication.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);
</script>

<template>
  <section id="route-content" class="page not-found" tabindex="-1">
    <p class="eyebrow">404</p>
    <h1>Page not found.</h1>
    <p>This page is not in the current publication build.</p>
    <div class="button-row">
      <RouterLink class="button button-primary" :to="{ name: 'home' }">Go home</RouterLink>
      <RouterLink class="button button-secondary" :to="{ name: 'results' }">
        View results
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.not-found {
  min-height: 72vh;
  padding: clamp(5rem, 11vw, 10rem) var(--gutter);
  background: var(--ink);
  color: white;
}

.not-found h1 {
  max-width: 10ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3.6rem, 9vw, 8rem);
  font-weight: 500;
  letter-spacing: -0.065em;
  line-height: 0.9;
}

.not-found > p:not(.eyebrow) {
  max-width: 38rem;
  margin: 2rem 0 0;
  color: rgb(255 255 255 / 63%);
  line-height: 1.65;
}

.not-found .button-secondary {
  color: white;
}
</style>
