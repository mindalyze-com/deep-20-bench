<script setup lang="ts">
import {
  computed,
  onActivated,
  provide,
  ref,
  watch,
} from "vue";
import { useRoute, type RouteLocationRaw } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import { getEpisode, getSubject } from "@/lib/api";
import {
  duration,
  money,
  number,
  percent,
  statusLabel,
} from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type { PublicTrialSummary, SubjectDocument } from "@/lib/types";
import {
  subjectWorkspaceKey,
  useRunWorkspace,
} from "@/lib/workspace-context";

import SubjectOverviewPane from "./SubjectOverviewPane.vue";

const route = useRoute();
const { run, subjects } = useRunWorkspace();
const document = ref<SubjectDocument | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const executionId = computed(() => String(route.params.executionId ?? ""));
const targetId = computed(() => String(route.params.targetId ?? ""));
const trialId = computed(() =>
  typeof route.params.trialId === "string" ? route.params.trialId : null,
);
const subject = computed(
  () =>
    subjects.value.find(
      (candidate) => candidate.target_id === targetId.value,
    ) ?? null,
);
const trials = computed(() => document.value?.trials ?? []);
const profile = computed(() => document.value?.profile ?? null);
const isSubjectOverview = computed(() => route.name === "subject");
const subjectIndex = computed(() =>
  subjects.value.findIndex((candidate) => candidate.target_id === targetId.value),
);

provide(subjectWorkspaceKey, {
  document,
  subject,
  loading,
});

const hasEpisode = (trial: PublicTrialSummary): boolean =>
  trial.status !== "infrastructure_failure";
const trialScoreWidth = (trial: PublicTrialSummary): string => {
  const maximum = Math.max(run.value?.max_questions ?? 1, 1);
  const score = Number(trial.penalized_questions ?? 0);
  return `${Math.min(100, Math.max(0, (score / maximum) * 100))}%`;
};

const episodeTo = (trial: PublicTrialSummary): RouteLocationRaw => ({
  name: "episode",
  params: {
    executionId: executionId.value,
    targetId: targetId.value,
    trialId: trial.trial_id,
  },
});

const applySubjectContext = (): void => {
  const currentRun = run.value;
  const currentSubject = subject.value;
  const index = subjectIndex.value;
  if (
    currentRun === null ||
    currentSubject === null ||
    index < 0 ||
    route.name !== "subject"
  ) {
    return;
  }
  const previousSubject = subjects.value[index - 1];
  const nextSubject = subjects.value[index + 1];
  setRouteContext({
    title: currentSubject.display_name,
    description: `${currentSubject.display_name} attempts in ${currentRun.model_name}.`,
    level: "Subject workspace",
    position: `${index + 1} of ${subjects.value.length}`,
    crumbs: [
      { label: "Results", to: { name: "results" } },
      {
        label: currentRun.model_name,
        to: {
          name: "run",
          params: { executionId: currentRun.execution_id },
        },
      },
      { label: currentSubject.display_name },
    ],
    previous: previousSubject
      ? {
          label: previousSubject.display_name,
          to: {
            name: "subject",
            params: {
              executionId: currentRun.execution_id,
              targetId: previousSubject.target_id,
            },
          },
        }
      : null,
    next: nextSubject
      ? {
          label: nextSubject.display_name,
          to: {
            name: "subject",
            params: {
              executionId: currentRun.execution_id,
              targetId: nextSubject.target_id,
            },
          },
        }
      : null,
  });
};

const load = async (): Promise<void> => {
  const requestedExecution = executionId.value;
  const requestedTarget = targetId.value;
  loading.value = true;
  error.value = null;
  try {
    const loaded = await getSubject(requestedExecution, requestedTarget);
    if (
      executionId.value !== requestedExecution ||
      targetId.value !== requestedTarget
    ) {
      return;
    }
    document.value = loaded;
    applySubjectContext();
  } catch (cause: unknown) {
    if (
      executionId.value !== requestedExecution ||
      targetId.value !== requestedTarget
    ) {
      return;
    }
    document.value = null;
    error.value =
      cause instanceof Error ? cause.message : "The subject could not be loaded.";
  } finally {
    if (
      executionId.value === requestedExecution &&
      targetId.value === requestedTarget
    ) {
      loading.value = false;
    }
  }
};

const warmEpisode = (trial: PublicTrialSummary): void => {
  if (!hasEpisode(trial)) return;
  void getEpisode(executionId.value, targetId.value, trial.trial_id);
};

watch([executionId, targetId], () => void load(), { immediate: true });
watch(() => route.name, applySubjectContext);
onActivated(applySubjectContext);
</script>

<template>
  <div
    class="subject-workspace"
    :class="{ 'has-episode': !isSubjectOverview }"
  >
    <LoadingState v-if="loading && document === null" label="Loading subject workspace" />
    <ErrorState v-else-if="error && document === null" :message="error" />

    <template v-else-if="run && subject && profile">
      <aside class="episode-rail" aria-label="Episodes for this subject">
        <header class="episode-rail-heading">
          <RouterLink
            class="mobile-run-back"
            :to="{ name: 'run', params: { executionId: run.execution_id } }"
          >
            <span aria-hidden="true">←</span>
            {{ run.model_name }}
          </RouterLink>
          <p class="eyebrow rail-section-label">
            <span aria-hidden="true">01</span>
            {{ subject.entity_type.replaceAll("_", " ") }}
          </p>
          <component :is="isSubjectOverview ? 'h1' : 'h2'">
            {{ subject.display_name }}
          </component>
          <p>{{ profile.subject_description }}</p>
          <div class="subject-score-line">
            <QuestionScore
              :score="subject.average_questions"
              :max-questions="run.max_questions"
              label="Average questions"
              variant="metric"
            />
            <dl>
              <div><dt>Solved</dt><dd>{{ subject.successful }}/{{ run.iterations }}</dd></div>
              <div><dt>Contract</dt><dd>{{ percent(subject.contract.compliance_rate) }}</dd></div>
            </dl>
          </div>
        </header>

        <nav class="episode-list" aria-label="Runs for this subject">
          <div class="episode-list-heading">
            <p class="eyebrow rail-section-label">
              <span aria-hidden="true">02</span>
              Runs
            </p>
            <strong>{{ trials.length }} attempts</strong>
          </div>
          <component
            :is="hasEpisode(trial) ? 'RouterLink' : 'span'"
            v-for="trial in trials"
            :key="trial.trial_id"
            :to="hasEpisode(trial) ? episodeTo(trial) : undefined"
            :aria-current="trialId === trial.trial_id ? 'page' : undefined"
            :class="{ disabled: !hasEpisode(trial) }"
            @mouseenter="warmEpisode(trial)"
            @focus="warmEpisode(trial)"
          >
            <span class="episode-index">{{ String(trial.trial_number).padStart(2, "0") }}</span>
            <span class="episode-copy">
              <strong>{{ statusLabel(trial.status) }}</strong>
              <small>
                {{ trial.counted_questions }} questions · {{ duration(trial.duration_ms) }}
                · {{ money(trial.cost_usd) }}
              </small>
              <span class="attempt-score-track" aria-hidden="true">
                <i
                  :class="trial.status"
                  :style="{ width: trialScoreWidth(trial) }"
                ></i>
              </span>
            </span>
            <span class="episode-score">{{ number(trial.penalized_questions) }}</span>
            <i
              class="episode-status"
              :class="[
                trial.status,
                { breached: trial.contract?.status === 'breached' },
              ]"
              aria-hidden="true"
            ></i>
          </component>
        </nav>

        <footer class="episode-rail-footer">
          <a
            v-if="profile.subject_reference_url"
            :href="profile.subject_reference_url"
            target="_blank"
            rel="noreferrer"
          >
            Subject reference <span aria-hidden="true">↗</span>
            <span class="visually-hidden">(opens in a new tab)</span>
          </a>
          <span>{{ money(trials.reduce((sum, trial) => sum + Number(trial.cost_usd), 0)) }} total</span>
        </footer>
      </aside>

      <section class="subject-stage" :aria-busy="loading">
        <div v-if="loading" class="workspace-progress" aria-hidden="true"></div>
        <SubjectOverviewPane v-if="isSubjectOverview" />
        <RouterView v-else />
      </section>
    </template>
  </div>
</template>

<style scoped>
.subject-workspace {
  display: grid;
  grid-template-columns: 21rem minmax(0, 1fr);
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.episode-rail {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border-right: 1px solid var(--line);
  background: #e9e6dd;
}

.episode-rail-heading {
  padding: clamp(1.25rem, 2.5vw, 2rem);
  border-bottom: 1px solid var(--line);
}

.mobile-run-back {
  display: none;
}

.episode-rail-heading .eyebrow {
  margin-bottom: 0.55rem;
  color: var(--blue-ink);
}

.rail-section-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rail-section-label span {
  font-family: var(--font-mono);
  opacity: 0.55;
}

.episode-rail-heading h1,
.episode-rail-heading h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.1rem, 3.5vw, 3.3rem);
  font-weight: 500;
  letter-spacing: -0.052em;
  line-height: 0.95;
}

.episode-rail-heading > p:not(.eyebrow) {
  display: -webkit-box;
  overflow: hidden;
  margin: 0.9rem 0 0;
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.subject-score-line {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: end;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line);
}

.subject-score-line :deep(.question-score strong) {
  font-size: 2.4rem;
}

.subject-score-line dl {
  display: grid;
  gap: 0.45rem;
  margin: 0;
}

.subject-score-line dl > div {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
}

.subject-score-line dt,
.subject-score-line dd {
  margin: 0;
  font-size: 0.61rem;
}

.subject-score-line dt {
  color: var(--muted);
}

.subject-score-line dd {
  font-weight: 760;
}

.episode-list {
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
}

.episode-list-heading {
  position: sticky;
  z-index: 2;
  top: 0;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  min-height: 42px;
  padding: 0.65rem 0.9rem;
  border-bottom: 1px solid var(--line);
  background: #dedbd2;
}

.episode-list-heading .eyebrow {
  margin: 0;
  color: var(--blue-ink);
}

.episode-list-heading > strong {
  color: var(--muted);
  font-size: 0.61rem;
  font-weight: 700;
}

.episode-list > a,
.episode-list > span {
  position: relative;
  display: grid;
  grid-template-columns: 1.7rem minmax(0, 1fr) auto auto;
  gap: 0.7rem;
  align-items: center;
  min-height: 62px;
  padding: 0.7rem 0.9rem;
  border-bottom: 1px solid var(--line-soft);
  color: var(--ink-soft);
  text-decoration: none;
}

.episode-list > a:hover {
  background: rgb(255 255 255 / 42%);
}

.episode-list > a[aria-current="page"] {
  background: var(--paper-bright);
}

.episode-list > a[aria-current="page"]::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--blue);
  content: "";
}

.episode-list > span.disabled {
  opacity: 0.52;
}

.episode-index {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 0.63rem;
}

.episode-copy {
  display: grid;
  min-width: 0;
  gap: 0.2rem;
}

.episode-copy strong {
  font-size: 0.73rem;
}

.episode-copy small {
  overflow: hidden;
  color: var(--muted);
  font-size: 0.6rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attempt-score-track {
  display: block;
  width: 100%;
  height: 3px;
  margin-top: 0.2rem;
  overflow: hidden;
  background: rgb(17 19 28 / 9%);
}

.attempt-score-track i {
  display: block;
  height: 100%;
  border-radius: 0;
  background: var(--blue);
}

.attempt-score-track i.model_failure {
  background: var(--coral);
}

.episode-score {
  font-size: 0.72rem;
  font-weight: 760;
  font-variant-numeric: tabular-nums;
}

.episode-status {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--line);
}

.episode-status.success {
  background: #6abf40;
}

.episode-status.model_failure {
  background: var(--coral);
}

.episode-status.breached {
  box-shadow: 0 0 0 2px var(--paper-bright), 0 0 0 3px var(--coral);
}

.episode-rail-footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.63rem;
}

.episode-rail-footer a {
  color: var(--blue-ink);
  font-weight: 700;
}

.subject-stage {
  position: relative;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--paper);
}

.workspace-progress {
  position: absolute;
  z-index: 20;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  overflow: hidden;
  background: rgb(78 100 255 / 16%);
}

.workspace-progress::after {
  display: block;
  width: 34%;
  height: 100%;
  background: var(--blue);
  animation: workspace-progress 0.75s ease-in-out infinite alternate;
  content: "";
}

@keyframes workspace-progress {
  from {
    transform: translateX(-20%);
  }
  to {
    transform: translateX(250%);
  }
}

@media (max-width: 1120px) {
  .subject-workspace {
    grid-template-columns: 18rem minmax(0, 1fr);
  }
}

@media (max-width: 1280px) {
  .mobile-run-back {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    margin-bottom: 1.3rem;
    color: var(--muted);
    font-size: 0.68rem;
    font-weight: 700;
    text-decoration: none;
  }
}

@media (max-height: 520px) and (min-width: 761px) {
  .episode-rail-heading {
    padding: 0.75rem 1rem;
  }

  .mobile-run-back {
    margin-bottom: 0.25rem;
  }

  .episode-rail-heading .eyebrow {
    margin-bottom: 0.3rem;
  }

  .episode-rail-heading h1,
  .episode-rail-heading h2 {
    font-size: 1.9rem;
  }

  .episode-rail-heading > p:not(.eyebrow) {
    display: none;
  }

  .subject-score-line {
    gap: 0.7rem;
    margin-top: 0.35rem;
    padding-top: 0.35rem;
  }

  .subject-score-line :deep(.question-score) {
    gap: 0.15rem;
  }

  .subject-score-line :deep(.question-score strong) {
    font-size: 2rem;
  }

  .subject-score-line :deep(.score-unit),
  .subject-score-line :deep(.score-scale) {
    display: none;
  }

  .episode-list-heading {
    min-height: 36px;
    padding: 0.45rem 0.75rem;
  }
}

@media (max-width: 760px) {
  .subject-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .episode-rail {
    border-right: 0;
  }

  .subject-workspace.has-episode .episode-rail {
    display: none;
  }

  .subject-workspace:not(.has-episode) .subject-stage {
    display: none;
  }

  .subject-workspace:not(.has-episode) .episode-rail {
    display: block;
    overflow-y: auto;
    overscroll-behavior-y: contain;
    scrollbar-width: thin;
  }

  .subject-workspace:not(.has-episode) .episode-list {
    overflow: visible;
  }

  .episode-rail-heading > p:not(.eyebrow) {
    font-size: 0.78rem;
    -webkit-line-clamp: 4;
  }
}

@media (max-height: 520px) and (max-width: 760px) {
  .episode-rail {
    grid-template-rows: auto minmax(0, 1fr);
  }

  .episode-rail-heading {
    padding: 0.55rem 0.8rem;
  }

  .mobile-run-back,
  .episode-rail-heading .eyebrow,
  .episode-rail-heading > p:not(.eyebrow),
  .subject-score-line,
  .episode-rail-footer {
    display: none;
  }

  .episode-rail-heading h1,
  .episode-rail-heading h2 {
    font-size: 1.6rem;
  }
}
</style>
