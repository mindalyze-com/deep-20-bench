<script setup lang="ts">
defineProps<{ message: string }>();

const reload = (): void => {
  window.location.reload();
};
</script>

<template>
  <section class="error-state" role="alert">
    <p class="eyebrow">Data unavailable</p>
    <h1>We could not load this page.</h1>
    <p>{{ message }}</p>
    <button class="button button-primary" type="button" @click="reload">
      Try again
    </button>
  </section>
</template>
