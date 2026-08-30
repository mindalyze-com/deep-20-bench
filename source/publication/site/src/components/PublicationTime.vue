<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import {
  date,
  dateTime,
  staticDateLabel,
  staticDateTimeLabel,
} from "@/lib/format";

const props = withDefaults(
  defineProps<{
    value: string;
    dateOnly?: boolean;
  }>(),
  { dateOnly: false },
);

let mounted = false;
const format = (value: string): string =>
  mounted
    ? props.dateOnly
      ? date(value)
      : dateTime(value)
    : props.dateOnly
      ? staticDateLabel(value)
      : staticDateTimeLabel(value);
const label = ref(format(props.value));

onMounted(() => {
  mounted = true;
  label.value = format(props.value);
});
watch(
  () => props.value,
  (value) => {
    label.value = format(value);
  },
);
</script>

<template>
  <time :datetime="value">{{ label }}</time>
</template>
