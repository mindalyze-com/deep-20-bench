<script setup lang="ts">
import {
  computed,
  onActivated,
  provide,
  ref,
  watch,
} from "vue";
import { useRoute } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import WorkspaceProgress from "@/components/WorkspaceProgress.vue";
import { getRun, getSubject } from "@/lib/api";
import { number, percent } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { RunDocument } from "@/lib/types";
import { runWorkspaceKey } from "@/lib/workspace-context";

import RunOverviewPane from "./RunOverviewPane.vue";

const route = useRoute();
const document = ref<RunDocument | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const executionId = computed(() => String(route.params.executionId ?? ""));
const run = computed(() => document.value?.run ?? null);
const subjects = computed(() => document.value?.subjects ?? []);
const selectedTargetId = computed(() =>
  typeof route.params.targetId === "string" ? route.params.targetId : null,
);
const isRunOverview = computed(() => route.name === "run");

provide(runWorkspaceKey, {
  document,
  run,
  subjects,
  loading,
});

const applyRunContext = (): void => {
  const current = run.value;
  if (current === null || route.name !== "run") return;
  setRouteContext({
    title: current.model_name,
    description: `Official Deep20Bench run ${current.execution_id}.`,
    level: "Run workspace",
    position: `${subjects.value.length} subjects`,
    crumbs: [
      { label: "Results", to: { name: "results" } },
      { label: current.model_name },
    ],
    previous: null,
    next: null,
  });
};

const load = async (): Promise<void> => {
  const requestedExecution = executionId.value;
  loading.value = true;
  error.value = null;
  try {
    const loaded = await getRun(requestedExecution);
    if (executionId.value !== requestedExecution) return;
    document.value = loaded;
    applyRunContext();
  } catch (cause: unknown) {
    if (executionId.value !== requestedExecution) return;
    document.value = null;
    error.value = cause instanceof Error ? cause.message : "The run could not be loaded.";
  } finally {
    if (executionId.value === requestedExecution) loading.value = false;
  }
};

const warmSubject = (targetId: string): void => {
  void getSubject(executionId.value, targetId);
};

watch(executionId, () => void load(), { immediate: true });
watch(() => route.name, applyRunContext);
onActivated(applyRunContext);
</script>

<template>
  <div
    id="route-content"
    class="benchmark-workspace"
    :class="{ 'is-run-overview': isRunOverview }"
    tabindex="-1"
  >
    <LoadingState v-if="loading && document === null" label="Loading run workspace" />
    <ErrorState v-else-if="error && document === null" :message="error" />

    <template v-else-if="run">
      <aside class="model-rail" aria-label="Run subjects">
        <div class="model-rail-heading">
          <RouterLink class="rail-back" :to="{ name: 'results' }">
            <span aria-hidden="true">←</span>
            Official results
          </RouterLink>
          <p class="eyebrow">Model under test</p>
          <h2>{{ run.model_name }}</h2>
          <div class="rail-score">
            <QuestionScore
              :score="run.question_score"
              :max-questions="run.max_questions"
              label="Question score"
              variant="metric"
              theme="dark"
            />
          </div>
        </div>

        <RouterLink
          class="run-overview-link"
          :to="{ name: 'run', params: { executionId: run.execution_id } }"
          :aria-current="isRunOverview ? 'page' : undefined"
        >
          <span class="rail-item-index" aria-hidden="true">00</span>
          <span>
            <strong>Run overview</strong>
            <small>{{ run.terminal_trials }} episodes · {{ percent(run.success_rate) }} success</small>
          </span>
        </RouterLink>

        <nav class="subject-rail-list" aria-label="Subjects in this run">
          <RouterLink
            v-for="(subject, index) in subjects"
            :key="subject.target_id"
            :to="{
              name: 'subject',
              params: {
                executionId: run.execution_id,
                targetId: subject.target_id,
              },
            }"
            :aria-current="
              selectedTargetId === subject.target_id ? 'page' : undefined
            "
            @mouseenter="warmSubject(subject.target_id)"
            @focus="warmSubject(subject.target_id)"
          >
            <span class="rail-item-index">{{ String(index + 1).padStart(2, "0") }}</span>
            <span class="rail-item-copy">
              <strong>{{ subject.display_name }}</strong>
              <small>
                {{ number(subject.average_questions) }} avg ·
                {{ subject.successful }}/{{ run.iterations }} solved
              </small>
            </span>
            <span
              class="rail-status"
              :class="{
                breached: subject.contract.status === 'breached',
                clean: subject.contract.status === 'clean',
              }"
              aria-hidden="true"
            ></span>
          </RouterLink>
        </nav>

        <footer class="model-rail-footer">
          <span>Run</span>
          <code>{{ run.execution_id }}</code>
        </footer>
      </aside>

      <section class="workspace-stage" :aria-busy="loading">
        <WorkspaceProgress :active="loading" />
        <RunOverviewPane v-if="isRunOverview" />
        <RouterView v-else />
      </section>
    </template>
  </div>
</template>

<style scoped>
.benchmark-workspace {
  display: grid;
  grid-template-columns: 18rem minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--paper);
}

.model-rail {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border-right: var(--rule-inverse-subtle);
  background: var(--surface-inverse);
  color: var(--text-inverse);
}

.model-rail-heading {
  padding: 1.4rem 1.35rem 1.25rem;
  border-bottom: var(--rule-inverse-subtle);
}

.rail-back {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 1.7rem;
  color: var(--text-inverse-subtle);
  font-size: var(--text-caption);
  font-weight: 700;
  text-decoration: none;
}

.rail-back:hover {
  color: var(--text-inverse);
}

.model-rail-heading .eyebrow {
  margin-bottom: 0.55rem;
  color: var(--acid);
  font-size: var(--text-caption);
}

.model-rail-heading h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.85rem, 2.7vw, 2.6rem);
  font-weight: 500;
  letter-spacing: -0.045em;
  line-height: 0.95;
}

.rail-score {
  margin-top: 1.2rem;
}

.rail-score :deep(.question-score) {
  gap: 0.15rem;
}

.rail-score :deep(.question-score strong) {
  font-size: 2.25rem;
}

.run-overview-link,
.subject-rail-list a {
  position: relative;
  display: grid;
  grid-template-columns: 1.6rem minmax(0, 1fr) auto;
  gap: 0.7rem;
  align-items: center;
  min-height: 58px;
  padding: 0.75rem 1rem;
  border-bottom: var(--rule-inverse-subtle);
  color: var(--text-inverse-muted);
  text-decoration: none;
}

.run-overview-link:hover,
.subject-rail-list a:hover {
  background: rgb(255 255 255 / 5%);
  color: var(--text-inverse);
}

.run-overview-link[aria-current="page"],
.subject-rail-list a[aria-current="page"] {
  background: var(--paper);
  color: var(--ink);
}

.run-overview-link[aria-current="page"]::before,
.subject-rail-list a[aria-current="page"]::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--acid);
  content: "";
}

.subject-rail-list {
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
}

.rail-item-index {
  color: currentColor;
  font-family: var(--font-mono);
  font-size: var(--text-caption);
  opacity: 0.52;
}

.rail-item-copy,
.run-overview-link > span:nth-child(2) {
  display: grid;
  min-width: 0;
  gap: 0.18rem;
}

.rail-item-copy strong,
.run-overview-link strong {
  overflow: hidden;
  font-size: var(--text-micro);
  font-weight: 740;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rail-item-copy small,
.run-overview-link small {
  overflow: hidden;
  color: currentColor;
  font-size: var(--text-caption);
  opacity: 0.82;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rail-status {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--line);
}

.rail-status.clean {
  background: var(--state-clean);
}

.rail-status.breached {
  background: var(--coral);
}

.model-rail-footer {
  display: grid;
  gap: 0.3rem;
  padding: 0.9rem 1rem 1rem;
  border-top: var(--rule-inverse-subtle);
  color: var(--text-inverse-subtle);
}

.model-rail-footer span {
  font-size: var(--text-caption);
  font-weight: 760;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.model-rail-footer code {
  overflow: hidden;
  font-size: var(--text-caption);
  text-overflow: ellipsis;
}

.workspace-stage {
  position: relative;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

@media (max-width: 1080px) {
  .benchmark-workspace {
    grid-template-columns: 15.5rem minmax(0, 1fr);
  }
}

@media (max-width: 1280px) {
  .benchmark-workspace:not(.is-run-overview) {
    grid-template-columns: minmax(0, 1fr);
  }

  .benchmark-workspace:not(.is-run-overview) .model-rail {
    display: none;
  }
}

@media (max-width: 760px) {
  .benchmark-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .model-rail {
    display: none;
  }
}
</style>
