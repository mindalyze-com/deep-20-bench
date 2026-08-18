<script setup lang="ts">
defineProps<{ href: string }>();
</script>

<template>
  <a :href="href" target="_blank" rel="noreferrer">
    Subject reference <span aria-hidden="true">↗</span>
    <span class="visually-hidden">(opens in a new tab)</span>
  </a>
</template>
