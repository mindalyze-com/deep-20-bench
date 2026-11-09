<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { durationAxisLabel, niceAxis, niceDurationAxis } from "@/lib/chart-axis";
import { dateTime, money, moneyEpisode, number } from "@/lib/format";
import { runRoute } from "@/lib/route-location";
import {
  groupHistoryMarkers,
  historyDifference,
  type HistoryChartRun,
  type HistoryMarkerGroup,
  type HistoryValueFormat,
} from "@/lib/run-history-chart";

const props = withDefaults(defineProps<{
  items: HistoryChartRun[];
  mode?: "dot" | "bar" | "scatter";
  xLabel: string;
  yLabel?: string;
  valueFormat?: HistoryValueFormat;
  color?: "blue" | "coral" | "acid" | "efficiency";
}>(), { mode: "dot", yLabel: "Question score", valueFormat: "number", color: "blue" });

const router = useRouter();
const plot = ref<HTMLDivElement | null>(null);
const tooltip = ref<HTMLDivElement | null>(null);
const width = ref(900);
let observer: ResizeObserver | null = null;
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    if (entry && entry.contentRect.width > 0) width.value = entry.contentRect.width;
  });
  if (plot.value) observer.observe(plot.value);
});
onBeforeUnmount(() => observer?.disconnect());

const latest = computed(() => props.items.filter(item => item.latest));
const earlier = computed(() => props.items.filter(item => !item.latest && latest.value.some(current => current.modelId === item.modelId)));
const all = computed(() => [...latest.value, ...earlier.value]);
const mobile = computed(() => width.value < 600);
const scatter = computed(() => props.mode === "scatter");
const height = computed(() => scatter.value ? 490 : Math.max(340, latest.value.length * 48 + 82));
const margins = computed(() => ({ left: scatter.value ? 62 : mobile.value ? 128 : 235, right: scatter.value ? 25 : mobile.value ? 42 : 65, top: 28, bottom: 54 }));
const innerWidth = computed(() => Math.max(40, width.value - margins.value.left - margins.value.right));
const innerHeight = computed(() => height.value - margins.value.top - margins.value.bottom);
const xAxis = computed(() => {
  const values = all.value.flatMap(run => [run.x, ...(run.lower === undefined ? [] : [run.lower]), ...(run.upper === undefined ? [] : [run.upper])]);
  const minimum = props.mode === "bar" ? 0 : Math.min(...values, Number.POSITIVE_INFINITY);
  const maximum = Math.max(...values, 1e-9);
  if (props.valueFormat === "duration") return niceDurationAxis(maximum, mobile.value ? 3 : 6);
  const padding = props.mode === "bar" ? 0 : Math.max(maximum - minimum, maximum * 0.05, 0.01) * 0.08;
  return niceAxis(Number.isFinite(minimum) ? Math.max(0, minimum - padding) : 0, maximum + padding, mobile.value ? 3 : 6);
});
const yAxis = computed(() => {
  const values = all.value.map(run => run.y ?? 0);
  return niceAxis(Math.max(0, Math.min(...values) - 1), Math.max(...values, 1) + 1, 6);
});
const ticks = (axis: { min: number; max: number; interval: number }): number[] =>
  Array.from({ length: Math.min(30, Math.round((axis.max - axis.min) / axis.interval) + 1) }, (_, index) => Number((axis.min + index * axis.interval).toPrecision(12)));
const xTicks = computed(() => ticks(xAxis.value));
const yTicks = computed(() => ticks(yAxis.value));
const x = (value: number): number => margins.value.left + (value - xAxis.value.min) / (xAxis.value.max - xAxis.value.min) * innerWidth.value;
const rowY = (run: HistoryChartRun): number => margins.value.top +
  (latest.value.findIndex(current => current.modelId === run.modelId) + 0.5) * innerHeight.value / Math.max(1, latest.value.length);
const y = (run: HistoryChartRun): number => scatter.value
  ? margins.value.top + (yAxis.value.max - (run.y ?? 0)) / (yAxis.value.max - yAxis.value.min) * innerHeight.value
  : rowY(run);
const axisLabel = (value: number): string => props.valueFormat === "duration" ? durationAxisLabel(value) :
  props.valueFormat === "episode-cost" ? moneyEpisode(value) : props.valueFormat === "currency" ? money(value) : number(value, 1);
const groups = computed(() => groupHistoryMarkers(earlier.value.map(run => ({ run, x: x(run.x), y: y(run) }))));
const latestFor = (run: HistoryChartRun): HistoryChartRun | undefined => latest.value.find(current => current.modelId === run.modelId);
const runDate = (run: HistoryChartRun): string => run.completedAt ? dateTime(run.completedAt) : "Date unavailable";
const href = (run: HistoryChartRun): string => router.resolve(runRoute(run.executionId)).href;
const delta = (run: HistoryChartRun): string => {
  const current = latestFor(run);
  return current ? historyDifference(run.x, current.x, props.valueFormat) : "-";
};
const scoreDelta = (run: HistoryChartRun): string => {
  const current = latestFor(run);
  return current?.y === undefined || run.y === undefined ? "-" : historyDifference(run.y,current.y,"number");
};
const description = (run: HistoryChartRun): string =>
  `${run.modelName}, ${runDate(run)}, ${run.latest ? "latest" : "earlier"} run: ${props.xLabel} ${run.xDisplay}${scatter.value ? `, ${props.yLabel} ${run.yDisplay}` : ""}${run.latest ? "" : `, earlier minus latest ${delta(run)}`}.`;

const hovered = ref<HistoryMarkerGroup | null>(null);
const pinned = ref(false);
const tooltipHeight = ref(230);
watch([hovered,width],async () => {
  await nextTick();
  if (tooltip.value) tooltipHeight.value = tooltip.value.getBoundingClientRect().height;
}, {flush:"post"});
let returnFocus: SVGElement | null = null;
const selectedModels = computed(() => new Set(hovered.value?.members.map(run => run.modelId) ?? []));
const paths = computed(() => latest.value.flatMap(current => {
  if (!selectedModels.value.has(current.modelId)) return [];
  const runs = all.value.filter(run => run.modelId === current.modelId)
    .sort((left, right) => (left.completedAt ?? "").localeCompare(right.completedAt ?? ""));
  return runs.length > 1 ? [runs.map(run => `${x(run.x)},${y(run)}`).join(" ")] : [];
}));
const tipStyle = computed(() => ({
  left: `${Math.max(0, Math.min((hovered.value?.x ?? 0) + 14, width.value - Math.min(width.value, 300)))}px`,
  top: `${Math.max(0, (hovered.value?.y ?? 0)+14+tooltipHeight.value <= height.value
    ? (hovered.value?.y ?? 0)+14 : (hovered.value?.y ?? 0)-tooltipHeight.value-14)}px`,
}));
const show = (group: HistoryMarkerGroup): void => { if (!pinned.value) hovered.value = group; };
const leave = (): void => {
  if (!pinned.value && !plot.value?.contains(document.activeElement)) hovered.value = null;
};
const close = (): void => { pinned.value = false; hovered.value = null; returnFocus?.focus(); };
const isTouch = (event: Event): boolean => "pointerType" in event && event.pointerType === "touch";
const pinGroup = async (event: Event, group: HistoryMarkerGroup): Promise<void> => {
  hovered.value = group;
  pinned.value = true;
  returnFocus = event.currentTarget as SVGElement;
  await nextTick();
  tooltip.value?.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
};
const openRun = (event: MouseEvent, run: HistoryChartRun): void => {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
  event.preventDefault();
  if (isTouch(event)) {
    void pinGroup(event,{x:x(run.x),y:y(run),members:[run]});
    return;
  }
  void router.push(runRoute(run.executionId));
};
const activateGroup = async (event: Event, group: HistoryMarkerGroup): Promise<void> => {
  if (group.members.length === 1 && !isTouch(event)) {
    void router.push(runRoute(group.members[0]!.executionId));
    return;
  }
  await pinGroup(event,group);
};
const coincides = (group: HistoryMarkerGroup): boolean => latest.value.some(run => Math.hypot(x(run.x) - group.x, y(run) - group.y) < 1.5);
const shortName = (run: HistoryChartRun): string => {
  const limit = mobile.value ? 21 : 32;
  return run.modelName.length > limit ? `${run.modelName.slice(0, limit - 1)}…` : run.modelName;
};
const components = computed(() => latest.value.find(run => run.components?.length)?.components ?? []);
const segmentStart = (run: HistoryChartRun, index: number): number => (run.components ?? []).slice(0, index).reduce((total, component) => total + component.value, 0);
</script>

<template>
  <figure class="run-history-chart" :class="[`history-color-${color}`, { 'history-scatter': scatter }]">
    <figcaption class="history-chart-legend">
      <span><i class="latest-marker" aria-hidden="true"></i>Latest run</span>
      <span><i class="earlier-marker" aria-hidden="true"></i>Earlier run</span>
      <small>Lower is better. Select a point to inspect its dated run.</small>
    </figcaption>
    <p class="history-chart-note">{{ scatter ? "Point numbers identify the models below." : "One row per model, ordered by its latest run." }} Hover or focus a point to follow its dates.</p>
    <ul v-if="components.length" class="history-component-key" aria-label="Cost components">
      <li v-for="component in components" :key="component.label"><i :style="{background:component.color}"></i>{{ component.label }}</li>
    </ul>
    <div ref="plot" class="history-plot" @pointerleave="leave" @keydown.esc.stop.prevent="close">
      <svg :viewBox="`0 0 ${width} ${height}`" :height="height" width="100%" role="group" :aria-label="`${xLabel} with earlier dated runs`">
        <g class="history-grid" aria-hidden="true">
          <g v-for="tick in xTicks" :key="tick">
            <line :x1="x(tick)" :x2="x(tick)" :y1="margins.top" :y2="height-margins.bottom" />
            <text :x="x(tick)" :y="height-margins.bottom+20" text-anchor="middle">{{ axisLabel(tick) }}</text>
          </g>
          <g v-if="scatter">
            <g v-for="tick in yTicks" :key="tick">
              <line :x1="margins.left" :x2="width-margins.right" :y1="margins.top+(yAxis.max-tick)/(yAxis.max-yAxis.min)*innerHeight" :y2="margins.top+(yAxis.max-tick)/(yAxis.max-yAxis.min)*innerHeight" />
              <text :x="margins.left-12" :y="margins.top+(yAxis.max-tick)/(yAxis.max-yAxis.min)*innerHeight+4" text-anchor="end">{{ number(tick,0) }}</text>
            </g>
            <text :transform="`translate(17 ${margins.top+innerHeight/2}) rotate(-90)`" text-anchor="middle">{{ yLabel }}</text>
          </g>
          <g v-else>
            <g v-for="run in latest" :key="run.executionId">
              <line :x1="margins.left" :x2="width-margins.right" :y1="y(run)" :y2="y(run)" class="row-guide" />
              <text :x="margins.left-16" :y="y(run)+4" text-anchor="end" class="history-model-label">{{ shortName(run) }}</text>
            </g>
          </g>
          <text :x="margins.left+innerWidth/2" :y="height-8" text-anchor="middle">{{ xLabel }}</text>
        </g>
        <g v-if="mode === 'bar'" aria-hidden="true">
          <g v-for="run in latest" :key="run.executionId">
            <template v-if="run.components?.length">
              <rect v-for="(component,index) in run.components" :key="component.label" :x="x(segmentStart(run,index))" :y="y(run)-6" :width="Math.max(0,x(segmentStart(run,index)+component.value)-x(segmentStart(run,index)))" height="12" :fill="component.color" />
            </template>
            <rect v-else :x="x(0)" :y="y(run)-6" :width="Math.max(0,x(run.x)-x(0))" height="12" rx="2" class="latest-bar" />
          </g>
        </g>
        <g v-if="mode === 'dot'" aria-hidden="true" class="history-confidence">
          <template v-for="run in all" :key="run.executionId">
            <line v-if="run.lower !== undefined && run.upper !== undefined" :x1="x(run.lower)" :x2="x(run.upper)" :y1="y(run)" :y2="y(run)" :class="{ historical: !run.latest, shown: hovered?.members.some(item=>item.executionId===run.executionId) }" />
          </template>
        </g>
        <g class="history-connections" aria-hidden="true"><polyline v-for="(path,index) in paths" :key="index" :points="path" /></g>
        <g v-for="(group,index) in groups" :key="index" role="button" tabindex="0" class="history-point earlier-point" :aria-label="group.members.length>1 ? `${group.members.length} overlapping earlier runs. Choose a date. ${group.members.map(description).join(' ')}` : description(group.members[0]!)" @pointerenter="show(group)" @focus="show(group)" @blur="leave" @click="activateGroup($event,group)" @keydown.enter.prevent="activateGroup($event,group)" @keydown.space.prevent="activateGroup($event,group)">
          <circle :cx="group.x" :cy="group.y" :r="coincides(group) ? 14 : group.members.length>1 ? 9 : 6" />
          <text v-if="group.members.length>1" :x="group.x+10" :y="group.y-10" class="overlap-count">×{{ group.members.length }}</text>
        </g>
        <a v-for="(run,index) in latest" :key="run.executionId" :href="href(run)" class="history-point latest-point" :aria-label="description(run)" @pointerenter="show({x:x(run.x),y:y(run),members:[run]})" @focus="show({x:x(run.x),y:y(run),members:[run]})" @blur="leave" @click="openRun($event,run)">
          <circle :cx="x(run.x)" :cy="y(run)" :r="scatter ? 10 : 7" />
          <text v-if="scatter" :x="x(run.x)" :y="y(run)+3.5" text-anchor="middle" class="point-number" aria-hidden="true">{{ index+1 }}</text>
          <text v-else :x="x(run.x)+13" :y="y(run)+4" class="latest-value" aria-hidden="true">{{ run.xDisplay }}</text>
        </a>
      </svg>
      <div v-if="hovered" ref="tooltip" class="history-point-tooltip" :class="{ pinned }" :style="tipStyle" :role="pinned ? 'dialog' : 'tooltip'" :aria-label="pinned ? 'Choose a dated run' : undefined">
        <button v-if="pinned" type="button" class="history-tooltip-close" aria-label="Close run choices" @click="close">×</button>
        <p v-if="hovered.members.length>1" class="history-tooltip-heading">{{ hovered.members.length }} overlapping runs{{ pinned ? ' - choose a date' : '' }}</p>
        <div v-for="run in hovered.members" :key="run.executionId" class="history-tooltip-run">
          <strong>{{ run.modelName }}</strong>
          <span>{{ runDate(run) }} · {{ run.latest ? 'Latest' : 'Earlier' }}</span>
          <b>{{ run.xDisplay }} <small>{{ xLabel }}</small></b>
          <span v-if="scatter">{{ run.yDisplay }} {{ yLabel }}</span>
          <span v-if="!run.latest">{{ delta(run) }} {{ xLabel }} compared with latest</span>
          <span v-if="!run.latest && scatter">{{ scoreDelta(run) }} {{ yLabel }} compared with latest</span>
          <span v-if="mode==='dot' && run.lower!==undefined">95% CI {{ number(run.lower) }}–{{ number(run.upper) }}</span>
          <span v-if="run.detail">{{ run.detail }}</span>
          <span v-for="component in run.components" :key="component.label">{{ component.label }}: {{ component.display }}</span>
          <RouterLink v-if="pinned" :to="runRoute(run.executionId)">Open this run →</RouterLink>
        </div>
      </div>
    </div>
    <ol v-if="scatter" class="history-model-key" aria-label="Latest model point numbers">
      <li v-for="(run,index) in latest" :key="run.executionId"><a :href="href(run)" @pointerenter="show({x:x(run.x),y:y(run),members:[run]})" @pointerleave="leave" @focus="show({x:x(run.x),y:y(run),members:[run]})" @blur="leave" @click="openRun($event,run)"><b>{{ index+1 }}</b>{{ run.modelName }}</a></li>
    </ol>
    <details v-if="earlier.length" class="history-values">
      <summary>Earlier runs ({{ earlier.length }}) - dates and values</summary>
      <p>Differences are earlier minus latest. Each date remains a separate result.</p>
      <ul>
        <li v-for="run in earlier" :key="run.executionId"><RouterLink :to="runRoute(run.executionId)">{{ run.modelName }} · {{ runDate(run) }}</RouterLink><span>{{ run.xDisplay }} {{ xLabel }}<template v-if="scatter"> · {{ run.yDisplay }} {{ yLabel }}</template> · {{ delta(run) }} {{ xLabel }} from latest<template v-if="scatter"> · {{ scoreDelta(run) }} {{ yLabel }} from latest</template></span><span v-if="run.detail">{{ run.detail }}</span></li>
      </ul>
    </details>
    <p v-else class="history-chart-note">No earlier qualifying runs are available in this edition.</p>
    <p v-if="mode==='dot'" class="history-chart-note">Lines show 95% confidence intervals. Earlier intervals appear when their marker is hovered or focused.</p>
  </figure>
</template>

<style scoped>
.run-history-chart { --history-accent:var(--blue); margin:0; padding:clamp(1rem,2.5vw,2rem); background:var(--paper-bright); }
.history-color-coral { --history-accent:var(--coral); }
.history-color-acid { --history-accent:var(--chart-acid); }
.history-color-efficiency { --history-accent:var(--result-efficiency); }
.history-chart-legend { display:flex; align-items:center; flex-wrap:wrap; gap:.6rem 1.2rem; color:var(--ink); font-size:.8rem; }
.history-chart-legend>span { display:inline-flex; gap:.4rem; align-items:center; white-space:nowrap; }
.history-chart-legend i { width:10px; height:10px; border-radius:50%; border:2px solid var(--history-accent); }
.latest-marker { background:var(--history-accent); }
.earlier-marker { opacity:.6; }
.history-chart-legend small,.history-chart-note { color:var(--muted); font-size:.75rem; }
.history-chart-note { margin:.65rem 0 .4rem; line-height:1.5; }
.history-plot { position:relative; }
.history-plot svg { display:block; overflow:visible; font-family:var(--font-sans); }
.history-grid line { stroke:var(--line-soft); stroke-width:1; }
.history-grid .row-guide { stroke-dasharray:2 5; opacity:.65; }
.history-grid text { font-size:11px; fill:var(--muted); }
.history-grid .history-model-label { fill:var(--ink); font-size:12px; font-weight:600; }
.latest-bar { fill:var(--history-accent); opacity:.75; }
.history-confidence line { stroke:var(--history-accent); stroke-width:2; opacity:.35; }
.history-confidence .historical { stroke-dasharray:4 3; opacity:0; }
.history-confidence .historical.shown { opacity:.65; }
.history-connections polyline { fill:none; stroke:var(--history-accent); stroke-width:1.5; stroke-dasharray:3 4; opacity:.5; pointer-events:none; }
.history-point { cursor:pointer; outline:none; }
.history-point:focus-visible circle { stroke:var(--ink); stroke-width:3; }
.earlier-point circle { fill:var(--paper-bright); stroke:var(--history-accent); stroke-width:2; stroke-opacity:.55; }
.earlier-point:hover circle { stroke-opacity:1; }
.earlier-point:focus-visible circle { stroke-opacity:1; }
.latest-point circle { fill:var(--history-accent); stroke:var(--paper-bright); stroke-width:2; }
.latest-point:hover circle { stroke:var(--ink); }
.latest-value { fill:var(--ink); font-size:12px; font-weight:650; }
.point-number { fill:white; font-size:9px; font-weight:700; }
.overlap-count { fill:var(--muted); font-size:10px; font-weight:600; }
.history-point-tooltip { position:absolute; z-index:5; width:min(300px,100%); padding:1rem; border:var(--rule-default); border-radius:8px; box-shadow:var(--shadow-floating); background:var(--paper-bright); color:var(--ink); font-size:.75rem; pointer-events:none; max-height:330px; overflow:auto; }
.history-point-tooltip.pinned { pointer-events:auto; }
.history-tooltip-run { display:grid; gap:.3rem; }
.history-tooltip-run+.history-tooltip-run { border-top:var(--rule-default); margin-top:.7rem; padding-top:.7rem; }
.history-tooltip-run>b { font-size:1.25rem; }
.history-tooltip-run>b small { font-size:.7rem; font-weight:400; }
.history-tooltip-run>span { color:var(--muted); line-height:1.4; }
.history-tooltip-run a { display:inline-flex; min-height:44px; align-items:center; color:var(--blue-ink); }
.history-tooltip-heading { margin:0 1.2rem .7rem 0; font-weight:600; }
.history-tooltip-close { position:absolute; top:0; right:0; width:44px; height:44px; border:0; background:transparent; font:inherit; font-size:1.25rem; cursor:pointer; }
.history-model-key { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:.2rem 1rem; padding:1rem 0; margin:0; list-style:none; }
.history-model-key a { display:flex; gap:.5rem; align-items:center; min-height:44px; color:var(--ink); text-decoration:none; font-size:.75rem; }
.history-model-key b { display:grid; place-items:center; flex:0 0 24px; height:24px; background:var(--history-accent); border-radius:50%; color:white; font-size:.65rem; }
.history-values { border-top:var(--rule-default); padding-top:.5rem; font-size:.8rem; }
.history-values summary { display:list-item; min-height:44px; align-content:center; cursor:pointer; color:var(--blue-ink); }
.history-values p { color:var(--muted); font-size:.75rem; }
.history-values ul { list-style:none; padding:0; margin:0; }
.history-values li { display:grid; gap:.3rem; padding:.6rem 0; border-top:var(--rule-subtle); }
.history-values a { display:inline-flex; align-items:center; min-height:44px; color:var(--blue-ink); }
.history-values li>span { color:var(--muted); font-size:.75rem; }
.history-component-key { display:flex; gap:.5rem 1rem; flex-wrap:wrap; list-style:none; margin:.7rem 0; padding:0; font-size:.7rem; color:var(--muted); }
.history-component-key li { display:flex; gap:.3rem; align-items:center; }
.history-component-key i { width:8px; height:8px; border-radius:50%; }
@media(max-width:600px) {
  .run-history-chart { padding:1rem .65rem; }
  .history-grid .history-model-label { font-size:10px; }
  .history-grid text { font-size:10px; }
  .latest-value { font-size:10px; }
  .history-model-key { grid-template-columns:1fr; }
  .history-chart-legend small { flex-basis:100%; }
}
</style>
