<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

import ModelRunLink from "@/components/ModelRunLink.vue";
import RankBadge from "@/components/RankBadge.vue";

defineProps<{
  rank: string | number | null;
  name: string;
  meta: string;
  to: RouteLocationRaw | null;
}>();
</script>

<template>
  <tr>
    <td class="rank-column"><RankBadge :rank="rank" /></td>
    <td class="model-column">
      <ModelRunLink v-if="to !== null" :to="to" :name="name" :meta="meta" />
      <template v-else>
        <strong>{{ name }}</strong>
        <small>{{ meta }}</small>
      </template>
    </td>
    <slot></slot>
  </tr>
</template>
