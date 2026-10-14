<script setup lang="ts">
withDefaults(defineProps<{
  rank: number | string | null;
  dark?: boolean;
  tied?: boolean;
  note?: string;
}>(), { dark: false, tied: false, note: undefined });
</script>

<template>
  <span
    class="rank-badge"
    :class="{ 'rank-badge--first': String(rank) === '1', 'rank-badge--dark': dark }"
    :data-rank="rank"
    :data-rank-tied="tied"
    :title="note"
  >
    <span aria-hidden="true">{{ tied ? '=' : '' }}{{ rank ?? '-' }}</span>
    <span class="visually-hidden">{{ rank === null || rank === '-' ? 'Unranked' : `${tied ? 'Shared rank' : 'Rank'} ${rank}` }}</span>
  </span>
</template>

<style scoped>
.rank-badge {
  display: inline-grid;
  flex: 0 0 auto;
  width: 1.75rem;
  height: 1.75rem;
  min-width: 1.75rem;
  min-height: 1.75rem;
  place-items: center;
  border: 1px solid var(--border-default);
  border-radius: 50%;
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: var(--font-weight-semibold);
  font-variant-numeric: tabular-nums;
  line-height: 1;
  vertical-align: middle;
}

.rank-badge--first {
  border-color: color-mix(in srgb, var(--blue-ink) 28%, transparent);
  background: color-mix(in srgb, var(--blue-ink) 6%, transparent);
  color: var(--blue-ink);
}

.rank-badge--dark {
  border-color: rgb(255 255 255 / 35%);
  color: white;
}

.rank-badge--dark.rank-badge--first {
  border-color: rgb(255 255 255 / 65%);
  background: rgb(255 255 255 / 12%);
}
</style>
