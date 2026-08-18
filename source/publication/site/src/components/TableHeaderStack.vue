<script setup lang="ts">
withDefaults(
  defineProps<{
    first: string;
    second: string;
    centered?: boolean;
  }>(),
  { centered: false },
);
</script>

<template>
  <span class="table-header-stack" :class="{ 'table-header-stack--center': centered }">
    <span>{{ first }}</span>
    <span>{{ second }}</span>
  </span>
</template>
