<script setup lang="ts">
import { computed, nextTick, onActivated, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ErrorState from "@/components/ErrorState.vue";
import EpisodeReliabilityPanel from "@/components/episode/EpisodeReliabilityPanel.vue";
import EpisodeSummary from "@/components/episode/EpisodeSummary.vue";
import EpisodeTranscriptPanel from "@/components/episode/EpisodeTranscriptPanel.vue";
import EpisodeUsagePanel from "@/components/episode/EpisodeUsagePanel.vue";
import LoadingState from "@/components/LoadingState.vue";
import { getEpisode } from "@/lib/api";
import { moneyEpisode, percent } from "@/lib/format";
import { setRouteContext } from "@/lib/route-context";
import type {
  EpisodeDocument,
  PublicTrialSummary,
} from "@/lib/types";
import {
  useRunWorkspace,
  useSubjectWorkspace,
} from "@/lib/workspace-context";

const route = useRoute();
const { document: runDocument, run } = useRunWorkspace();
const { document: subjectDocument, subject } = useSubjectWorkspace();
const episodeDocument = ref<EpisodeDocument | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
type EpisodeTab = "transcript" | "reliability" | "usage";
const activeTab = ref<EpisodeTab>("transcript");
const episodeTabs: EpisodeTab[] = ["transcript", "reliability", "usage"];

const executionId = computed(() => String(route.params.executionId ?? ""));
const targetId = computed(() => String(route.params.targetId ?? ""));
const trialId = computed(() => String(route.params.trialId ?? ""));
const trial = computed(
  () =>
    subjectDocument.value?.trials.find(
      (candidate) => candidate.trial_id === trialId.value,
    ) ?? null,
);
const episode = computed(() => episodeDocument.value?.episode ?? null);
const episodeTrials = computed(() =>
  (subjectDocument.value?.trials ?? []).filter(
    (candidate) => candidate.status !== "infrastructure_failure",
  ),
);
const episodeIndex = computed(() =>
  episodeTrials.value.findIndex(
    (candidate) => candidate.trial_id === trialId.value,
  ),
);

const selectEpisodeTab = (tab: EpisodeTab, focus = false): void => {
  activeTab.value = tab;
  if (!focus) return;
  void nextTick(() => {
    document.getElementById(`episode-tab-${tab}`)?.focus();
  });
};

const onEpisodeTabKeydown = (event: KeyboardEvent, current: EpisodeTab): void => {
  const currentIndex = episodeTabs.indexOf(current);
  let nextIndex: number | null = null;
  if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % episodeTabs.length;
  else if (event.key === "ArrowLeft") {
    nextIndex = (currentIndex - 1 + episodeTabs.length) % episodeTabs.length;
  } else if (event.key === "Home") nextIndex = 0;
  else if (event.key === "End") nextIndex = episodeTabs.length - 1;
  if (nextIndex === null) return;
  event.preventDefault();
  const next = episodeTabs[nextIndex];
  if (next !== undefined) selectEpisodeTab(next, true);
};

const episodeTo = (candidate: PublicTrialSummary) => ({
  name: "episode" as const,
  params: {
    executionId: executionId.value,
    targetId: targetId.value,
    trialId: candidate.trial_id,
  },
});

const applyRouteContext = (): void => {
  const currentRun = run.value;
  const currentSubject = subject.value;
  const currentTrial = trial.value;
  const index = episodeIndex.value;
  if (
    currentRun === null ||
    currentSubject === null ||
    currentTrial === null ||
    index < 0
  ) {
    return;
  }
  const previousTrial = episodeTrials.value[index - 1];
  const nextTrial = episodeTrials.value[index + 1];
  setRouteContext({
    title: `Episode ${currentTrial.trial_number} · ${currentSubject.display_name}`,
    description: `Questions, answers, and Oracle evidence for finding ${currentSubject.display_name}.`,
    level: "Episode",
    position: `${index + 1} of ${episodeTrials.value.length}`,
    crumbs: [
      { label: "Results", to: { name: "results" } },
      {
        label: currentRun.model_name,
        to: {
          name: "run",
          params: { executionId: currentRun.execution_id },
        },
      },
      {
        label: currentSubject.display_name,
        to: {
          name: "subject",
          params: {
            executionId: currentRun.execution_id,
            targetId: currentSubject.target_id,
          },
        },
      },
      { label: `Episode ${currentTrial.trial_number}` },
    ],
    previous: previousTrial
      ? { label: `Episode ${previousTrial.trial_number}`, to: episodeTo(previousTrial) }
      : null,
    next: nextTrial
      ? { label: `Episode ${nextTrial.trial_number}`, to: episodeTo(nextTrial) }
      : null,
  });
};

const load = async (): Promise<void> => {
  const requestedExecution = executionId.value;
  const requestedTarget = targetId.value;
  const requestedTrial = trialId.value;
  loading.value = true;
  error.value = null;
  activeTab.value = "transcript";
  episodeDocument.value = null;
  try {
    const loadedEpisode = await getEpisode(
      requestedExecution,
      requestedTarget,
      requestedTrial,
    );
    if (
      executionId.value !== requestedExecution ||
      targetId.value !== requestedTarget ||
      trialId.value !== requestedTrial
    ) {
      return;
    }
    if (
      !runDocument.value?.subjects.some(
        (candidate) => candidate.target_id === requestedTarget,
      ) ||
      !subjectDocument.value?.trials.some(
        (candidate) => candidate.trial_id === requestedTrial,
      )
    ) {
      throw new Error("The requested episode is not part of this run.");
    }
    episodeDocument.value = loadedEpisode;
    applyRouteContext();
  } catch (cause: unknown) {
    if (
      executionId.value !== requestedExecution ||
      targetId.value !== requestedTarget ||
      trialId.value !== requestedTrial
    ) {
      return;
    }
    episodeDocument.value = null;
    error.value = cause instanceof Error ? cause.message : "The episode could not be loaded.";
  } finally {
    if (
      executionId.value === requestedExecution &&
      targetId.value === requestedTarget &&
      trialId.value === requestedTrial
    ) {
      loading.value = false;
    }
  }
};

watch([executionId, targetId, trialId], () => void load(), { immediate: true });
onActivated(applyRouteContext);
</script>

<template>
  <div class="episode-view">
    <LoadingState v-if="loading" label="Loading episode" />
    <ErrorState v-else-if="error" :message="error" />

    <template v-else-if="run && subject && trial && episode">
      <EpisodeSummary
        :run="run"
        :subject="subject"
        :trial="trial"
        :episode="episode"
      />

      <nav class="episode-tabs" aria-label="Episode detail views" role="tablist">
        <button
          id="episode-tab-transcript"
          type="button"
          role="tab"
          aria-controls="transcript"
          :aria-selected="activeTab === 'transcript'"
          :tabindex="activeTab === 'transcript' ? 0 : -1"
          @click="selectEpisodeTab('transcript')"
          @keydown="onEpisodeTabKeydown($event, 'transcript')"
        >
          <span>Transcript</span>
          <small>{{ episode.turns.length }} turns</small>
        </button>
        <button
          id="episode-tab-reliability"
          type="button"
          role="tab"
          aria-controls="reliability"
          :aria-selected="activeTab === 'reliability'"
          :tabindex="activeTab === 'reliability' ? 0 : -1"
          @click="selectEpisodeTab('reliability')"
          @keydown="onEpisodeTabKeydown($event, 'reliability')"
        >
          <span>Reliability</span>
          <small>{{ episode.contract.violations }} violations</small>
        </button>
        <button
          id="episode-tab-usage"
          type="button"
          role="tab"
          aria-controls="technical"
          :aria-selected="activeTab === 'usage'"
          :tabindex="activeTab === 'usage' ? 0 : -1"
          @click="selectEpisodeTab('usage')"
          @keydown="onEpisodeTabKeydown($event, 'usage')"
        >
          <span>Models & usage</span>
          <small>{{ moneyEpisode(episode.total_cost_usd) }}</small>
        </button>
      </nav>

      <section
        v-if="episode.contract.status === 'breached'"
        class="contract-warning"
        aria-labelledby="episode-contract-heading"
      >
        <div class="content-inner warning">
          <div>
            <p class="eyebrow">Reliability warning</p>
            <h2 id="episode-contract-heading">Model broke the output contract.</h2>
          </div>
          <div>
            <p>
              The Guesser produced {{ episode.contract.violations }} invalid structured
              responses. Violations before the limit consumed counted turns. The fixed feedback
              disclosed only the public action format, never whether an attempted answer was
              correct.
            </p>
            <dl class="warning-facts">
              <div><dt>Compliance</dt><dd>{{ percent(episode.contract.compliance_rate) }}</dd></div>
              <div><dt>Violations</dt><dd>{{ episode.contract.violations }}</dd></div>
              <div><dt>Turn penalties</dt><dd>{{ episode.contract.counted_penalties }}</dd></div>
            </dl>
          </div>
        </div>
      </section>

      <div class="episode-content">
        <EpisodeTranscriptPanel
          v-show="activeTab === 'transcript'"
          :episode="episode"
        />

        <EpisodeReliabilityPanel
          v-show="activeTab === 'reliability'"
          :episode="episode"
        />

        <EpisodeUsagePanel
          v-show="activeTab === 'usage'"
          :run="run"
          :trial="trial"
          :episode="episode"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
.warning-facts dt {
  color: var(--muted);
  font-size: var(--text-caption);
  font-weight: 780;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.contract-warning {
  padding: clamp(2rem, 5vw, 4rem) var(--gutter);
  border-block: var(--border-width) solid var(--state-danger);
  background: var(--surface-danger-soft);
}

.warning > div:last-child > p {
  margin: 0;
  line-height: 1.65;
}

.warning-facts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  margin: 1.5rem 0 0;
  border: var(--rule-default);
}

.warning-facts div {
  padding: 0.9rem;
  border-right: var(--rule-default);
}

.warning-facts div:last-child {
  border-right: 0;
}

.warning-facts dd {
  margin: 0.35rem 0 0;
  font-weight: 760;
}

.episode-view {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--paper);
}

.episode-view > .loading-state,
.episode-view > .error-state {
  grid-row: 1 / -1;
}

.episode-tabs {
  display: flex;
  min-width: 0;
  overflow-x: auto;
  border-bottom: var(--rule-default);
  background: var(--surface-rail);
  scrollbar-width: thin;
}

.episode-tabs button {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  gap: 0.18rem;
  min-width: 9.5rem;
  padding: 0.75rem 1.1rem 0.7rem;
  border: 0;
  border-right: var(--rule-default);
  color: var(--muted);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.episode-tabs button:hover {
  color: var(--ink);
  background: rgb(255 255 255 / 35%);
}

.episode-tabs button[aria-selected="true"] {
  color: var(--ink);
  background: var(--paper);
}

.episode-tabs button[aria-selected="true"]::after {
  position: absolute;
  right: 0.9rem;
  bottom: -1px;
  left: 0.9rem;
  height: 3px;
  background: var(--blue);
  content: "";
}

.episode-tabs span {
  font-size: 0.72rem;
  font-weight: 760;
}

.episode-tabs small {
  font-size: var(--text-caption);
  opacity: 0.7;
}

.contract-warning {
  display: none;
}

.episode-content {
  min-height: 0;
  overflow: hidden;
}

@media (max-width: 760px) {
  .episode-view {
    display: block;
    height: auto;
    min-height: 0;
    overflow: visible;
  }

  .episode-tabs {
    overflow: hidden;
  }

  .episode-tabs button {
    flex: 1 1 0;
    min-width: 0;
    padding: 0.68rem 0.55rem 0.64rem;
  }

  .episode-tabs span {
    overflow: hidden;
    font-size: var(--text-caption);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .episode-tabs small {
    overflow: hidden;
    font-size: var(--text-caption);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .episode-content {
    overflow: visible;
  }
}

@media (max-height: 520px) {
  .episode-hero {
    display: none;
  }

  .episode-tabs button {
    padding-block: 0.55rem;
  }
}
</style>
