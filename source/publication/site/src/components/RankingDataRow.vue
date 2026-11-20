<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

import ModelRunLink from "@/components/ModelRunLink.vue";
import RankBadge from "@/components/RankBadge.vue";

defineProps<{
  rank: string | number | null;
  date?: string | null;
  name: string;
  meta: string;
  to: RouteLocationRaw | null;
}>();
</script>

<template>
  <tr>
    <td class="rank-column"><RankBadge :rank="rank" /></td>
    <td class="model-column">
      <ModelRunLink v-if="to !== null" :to="to" :name="name" :meta="meta" :date="date" />
      <template v-else>
        <strong>{{ name }}</strong>
        <small>{{ meta }}</small>
      </template>
    </td>
    <slot></slot>
  </tr>
</template>

<style scoped>.run-date { font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem; white-space: nowrap; }</style>
