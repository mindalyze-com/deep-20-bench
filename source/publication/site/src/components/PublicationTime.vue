<script setup lang="ts">
import { computed } from "vue";

import { date, dateTime } from "@/lib/format";

const props = withDefaults(
  defineProps<{
    value: string;
    dateOnly?: boolean;
  }>(),
  { dateOnly: false },
);

const label = computed(() => (props.dateOnly ? date(props.value) : dateTime(props.value)));
</script>

<template>
  <time :datetime="value">{{ label }}</time>
</template>
