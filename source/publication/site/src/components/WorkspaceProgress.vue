<script setup lang="ts">
defineProps<{
  active: boolean;
}>();
</script>

<template>
  <div v-if="active" class="workspace-progress" aria-hidden="true"></div>
</template>
