<template>
  <div class="efficiency-marker-legend" aria-label="Chart marker meanings">
    <span>
      <i class="marker-symbol marker-symbol--pareto" aria-hidden="true"></i>
      <span>
        <strong>Diamond</strong>
        Pareto-efficient - no other model is both cheaper and better
      </span>
    </span>
    <span>
      <i class="marker-symbol" aria-hidden="true"></i>
      <span><strong>Circle</strong> Other ranked model</span>
    </span>
  </div>
</template>

<style scoped>
.efficiency-marker-legend {
  display: grid;
  gap: 0.7rem;
  color: var(--muted);
  font-size: var(--text-micro);
  line-height: 1.4;
}

.efficiency-marker-legend > span {
  display: grid;
  grid-template-columns: 0.75rem minmax(0, 1fr);
  gap: 0.55rem;
  align-items: start;
}

.efficiency-marker-legend strong {
  display: block;
  color: var(--ink-soft);
}

.marker-symbol {
  width: 0.65rem;
  height: 0.65rem;
  margin-top: 0.2rem;
  border: var(--rule-strong);
  border-radius: 50%;
  background: var(--result-efficiency);
}

.marker-symbol--pareto {
  border-radius: 0;
  transform: rotate(45deg);
}
</style>
