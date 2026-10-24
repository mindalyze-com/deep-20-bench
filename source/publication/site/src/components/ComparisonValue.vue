<script setup lang="ts">
import { computed } from "vue";
import { compareDecimal } from "@/lib/exact-decimal";
import { number } from "@/lib/format";
import { formatValue, subtractValue, type ComparisonValue, type ValueFormat, type ValueMark } from "@/lib/comparison";

const props = withDefaults(defineProps<{
  value: ComparisonValue | null;
  format: ValueFormat;
  mark?: ValueMark;
  baseline?: ComparisonValue | null;
  digits?: number;
}>(), { mark: null, baseline: null, digits: 2 });
const delta = computed(() => {
  if (props.value === null || props.baseline === null) return null;
  const difference = subtractValue(props.value, props.baseline);
  const sign = compareDecimal(difference.numerator, "0");
  const absolute = { ...difference, numerator: difference.numerator.replace(/^-/, "") };
  const formatted = props.format === "percent"
    ? number(Number(absolute.numerator) / absolute.denominator * 100, 1)
    : formatValue(absolute, props.format, props.digits);
  return `${sign > 0 ? "+" : sign < 0 ? "−" : ""}${formatted}`;
});
</script>

<template>
  <span class="comparison-value" :class="{ 'is-unavailable': value === null }">
    <span class="comparison-primary" :class="{ 'has-leading': !!$slots.leading }">
      <slot name="leading" />
      <strong>{{ formatValue(value, format, digits) }}</strong>
      <span v-if="mark" class="visually-hidden">
        {{ mark === 'best' ? 'Best' : mark === 'worst' ? 'Worst' : 'Tie' }}
      </span>
    </span>
    <small v-if="delta !== null" class="comparison-delta">{{ delta }}<template v-if="format === 'percent'">{{ ' ' }}<abbr title="percentage points"><span aria-hidden="true">pp</span><span class="visually-hidden">percentage points</span></abbr></template> vs reference</small>
    <slot />
  </span>
</template>

<style scoped>
.comparison-value { display: flex; flex-direction: column; align-items: flex-end; gap: 0.3rem; min-width: 0; }
.comparison-primary { display: flex; align-items: center; gap: 0.35rem; max-width: 100%; }
.comparison-primary.has-leading { width: 100%; justify-content: space-between; flex-wrap: wrap; }
.comparison-primary.has-leading strong { margin-inline-start: auto; white-space: nowrap; }
.comparison-value strong { font-variant-numeric: tabular-nums; font-weight: 600; line-height: 1.4; }
.comparison-value small { font-size: 0.75rem; line-height: 1.4; }
.comparison-delta, .is-unavailable { color: var(--text-secondary); }
.comparison-delta abbr { text-decoration: none; }
</style>
