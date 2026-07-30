<script setup lang="ts">
withDefaults(defineProps<{ label?: string }>(), { label: "Loading publication data" });
</script>

<template>
  <div class="loading-state" role="status">
    <span aria-hidden="true"></span>
    <p>{{ label }}…</p>
  </div>
</template>
