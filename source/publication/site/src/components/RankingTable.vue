<script setup lang="ts">
withDefaults(defineProps<{ label: string; minWidth?: string; tableClass?: string }>(), {
  minWidth: "760px",
  tableClass: "",
});
</script>

<template>
  <div
    class="table-wrap ranking-table-wrap results-table-wrap"
    :aria-label="label"
  >
    <table
      class="data-table ranking-table results-table"
      :class="tableClass"
      :style="{ minWidth }"
    >
      <caption class="visually-hidden">{{ label }}</caption>
      <slot></slot>
    </table>
  </div>
</template>
