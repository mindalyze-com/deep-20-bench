<script setup lang="ts">
import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";

defineProps<{
  loading: boolean;
  loadingLabel: string;
  error: string | null;
  empty: boolean;
}>();
</script>

<template>
  <LoadingState v-if="loading" :label="loadingLabel" />
  <ErrorState v-else-if="error !== null" :message="error" />
  <section v-else-if="empty" class="content-section empty-state">
    <div class="content-inner">
      <slot name="empty"></slot>
    </div>
  </section>
  <section v-else class="content-section">
    <div class="content-inner">
      <slot></slot>
    </div>
  </section>
</template>
