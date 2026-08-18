<script setup lang="ts">
import { computed } from "vue";

import ContractStatusCard from "@/components/ContractStatusCard.vue";
import MetricGrid, { type MetricGridItem } from "@/components/MetricGrid.vue";
import SubjectReferenceLink from "@/components/SubjectReferenceLink.vue";
import QuestionScore from "@/components/QuestionScore.vue";
import {
  contractExampleRoute,
  firstBreachedTrial,
} from "@/lib/contract-example";
import { contractPercent, number } from "@/lib/format";
import {
  useRunWorkspace,
  useSubjectWorkspace,
} from "@/lib/workspace-context";

const { run } = useRunWorkspace();
const { document, subject } = useSubjectWorkspace();

const exampleTo = computed(() => {
  const currentRun = run.value;
  const currentSubject = subject.value;
  const currentDocument = document.value;
  if (currentRun === null || currentSubject === null || currentDocument === null) {
    return null;
  }
  const example = firstBreachedTrial(currentDocument.trials);
  return example === null
    ? null
    : contractExampleRoute(
        currentRun.execution_id,
        currentSubject.target_id,
        example.trial_id,
      );
});

const facts = computed<MetricGridItem[]>(() => {
  const currentSubject = subject.value;
  const currentDocument = document.value;
  if (currentSubject === null || currentDocument === null) return [];
  return [
    {
      key: "episodes",
      label: "Episodes",
      value: currentDocument.trials.length,
    },
    {
      key: "successful",
      label: "Successful",
      value: currentSubject.successful,
    },
    {
      key: "average",
      label: "Average",
      value: number(currentSubject.average_questions),
    },
    {
      key: "contract",
      label: "Contract",
      value: contractPercent(
        currentSubject.contract.compliance_rate,
        currentSubject.contract.violations,
      ),
      tone: currentSubject.contract.status === "breached" ? "danger" : "default",
      linkLabel: exampleTo.value === null ? undefined : "View one example",
      to: exampleTo.value ?? undefined,
    },
  ];
});
</script>

<template>
  <article v-if="run && subject && document" class="subject-overview-pane">
    <div class="subject-overview-inner workspace-detail-boundary">
      <header>
        <p class="eyebrow">Subject overview</p>
        <h2>{{ subject.display_name }}</h2>
        <p>{{ document.profile.subject_description }}</p>
        <SubjectReferenceLink
          v-if="document.profile.subject_reference_url"
          :href="document.profile.subject_reference_url"
        />
      </header>

      <div class="subject-score-card">
        <QuestionScore
          :score="subject.average_questions"
          :max-questions="run.max_questions"
          label="Average questions"
          explain
        />
        <p>
          The score averages all {{ document.trials.length }} penalized trial values for this
          subject.
        </p>
      </div>

      <MetricGrid
        class="subject-facts"
        :items="facts"
        label="Subject summary"
        :max-columns="4"
        density="compact"
      />

      <ContractStatusCard
        :contract="subject.contract"
        affected-unit="attempts"
        heading-level="h3"
        :example-to="exampleTo"
      />

      <aside class="episode-prompt">
        <span aria-hidden="true">↖</span>
        <div>
          <strong>Choose an episode.</strong>
          <p>Open it to inspect the transcript, reliability, and usage.</p>
        </div>
      </aside>
    </div>
  </article>
</template>

<style scoped>
.subject-overview-pane {
  height: 100%;
  overflow-y: auto;
  padding: var(--workspace-gutter);
  scrollbar-gutter: stable;
}

.subject-overview-inner {
  --subject-overview-display-size: var(--text-workspace-title);
  --subject-overview-display-line-height: 0.92;

  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(16rem, 0.85fr);
  background: transparent;
  gap: var(--workspace-panel-gap);
}

.subject-overview-inner > * {
  min-width: 0;
  background: var(--paper-bright);
  padding: var(--workspace-panel-padding);
}

.subject-overview-inner > header,
.subject-score-card,
.episode-prompt {
  border: var(--rule-default);
}

.subject-overview-inner > header {
  min-height: clamp(15rem, 27vw, 18rem);
}

.subject-overview-inner h2 {
  max-width: 11ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--subject-overview-display-size);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.06em;
  line-height: var(--subject-overview-display-line-height);
}

.subject-overview-inner header > p:not(.eyebrow) {
  max-width: 38rem;
  margin: 1.4rem 0 0;
  color: var(--muted);
  line-height: 1.7;
}

.subject-overview-inner header > a {
  display: inline-block;
  margin-top: 1.2rem;
  color: var(--blue-ink);
  font-size: 0.72rem;
  font-weight: var(--font-weight-bold);
}

.subject-score-card {
  border-top: var(--border-emphasis-width) solid var(--blue);
}

.subject-score-card :deep(.question-score strong) {
  font-size: var(--subject-overview-display-size);
  line-height: var(--subject-overview-display-line-height);
}

.subject-score-card > p {
  margin: 1.2rem 0 0;
  color: var(--muted);
  font-size: 0.75rem;
  line-height: 1.55;
}

.subject-facts {
  grid-column: 1 / -1;
  margin: 0;
}

.episode-prompt p {
  margin: 0.85rem 0 0;
  color: var(--muted);
  font-size: 0.76rem;
  line-height: 1.6;
}

.episode-prompt {
  display: flex;
  gap: 1rem;
  align-items: start;
}

.episode-prompt > span {
  color: var(--blue);
  font-size: 1.4rem;
}

.episode-prompt strong {
  font-size: 0.8rem;
}

@media (max-width: 1020px) {
  .subject-overview-inner {
    grid-template-columns: 1fr;
  }

  .subject-facts {
    grid-column: auto;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .subject-overview-pane {
    height: auto;
    overflow: visible;
    padding: var(--workspace-gutter);
    scrollbar-gutter: auto;
  }

  .subject-overview-inner > header {
    min-height: 0;
  }
}
</style>
