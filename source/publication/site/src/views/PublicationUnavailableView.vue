<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
const route = useRoute();
const router = useRouter();
const retry = (): void => {
  const destination = route.query.retry;
  void router.replace(typeof destination === "string" && destination.startsWith("/")
    && !destination.startsWith("//") ? destination : "/");
};
</script>
<template>
  <div id="route-content" class="page content-section" tabindex="-1">
    <div class="content-inner">
      <section class="error-state" role="alert">
        <h1>Publication unavailable</h1>
        <p>The edition settings could not be loaded. Try again.</p>
        <button class="button button-primary" type="button" @click="retry">Try again</button>
      </section>
    </div>
  </div>
</template>
