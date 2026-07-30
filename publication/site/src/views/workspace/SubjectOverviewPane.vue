<script setup lang="ts">
import QuestionScore from "@/components/QuestionScore.vue";
import { number, percent } from "@/lib/format";
import {
  useRunWorkspace,
  useSubjectWorkspace,
} from "@/lib/workspace-context";

const { run } = useRunWorkspace();
const { document, subject } = useSubjectWorkspace();
</script>

<template>
  <article v-if="run && subject && document" class="subject-overview-pane">
    <div class="subject-overview-inner">
      <header>
        <p class="eyebrow">Subject overview</p>
        <h2>{{ subject.display_name }}</h2>
        <p>{{ document.profile.subject_description }}</p>
        <a
          v-if="document.profile.subject_reference_url"
          :href="document.profile.subject_reference_url"
          target="_blank"
          rel="noreferrer"
        >
          Subject reference <span aria-hidden="true">↗</span>
          <span class="visually-hidden">(opens in a new tab)</span>
        </a>
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

      <dl class="subject-facts">
        <div><dt>Episodes</dt><dd>{{ document.trials.length }}</dd></div>
        <div><dt>Successful</dt><dd>{{ subject.successful }}</dd></div>
        <div><dt>Average</dt><dd>{{ number(subject.average_questions) }}</dd></div>
        <div><dt>Contract</dt><dd>{{ percent(subject.contract.compliance_rate) }}</dd></div>
      </dl>

      <section
        class="subject-reliability"
        :class="subject.contract.status"
        aria-labelledby="subject-reliability-title"
      >
        <p class="eyebrow">Reliability</p>
        <h3 id="subject-reliability-title">
          {{
            subject.contract.status === "breached"
              ? "Output contract breached."
              : "Output contract clean."
          }}
        </h3>
        <p v-if="subject.contract.status === 'breached'">
          {{ subject.contract.violations }} invalid outputs affected
          {{ subject.contract.affected_trials }} attempts and consumed
          {{ subject.contract.counted_penalties }} counted turns.
        </p>
        <p v-else>
          All {{ subject.contract.evaluated_outputs }} evaluated outputs matched the public
          structured-action contract.
        </p>
      </section>

      <aside class="episode-prompt">
        <span aria-hidden="true">↖</span>
        <div>
          <strong>Select an episode.</strong>
          <p>Open an attempt to inspect its transcript, reliability, and usage.</p>
        </div>
      </aside>
    </div>
  </article>
</template>

<style scoped>
.subject-overview-pane {
  height: 100%;
  overflow-y: auto;
  padding: clamp(2rem, 5vw, 5rem);
  scrollbar-gutter: stable;
}

.subject-overview-inner {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(16rem, 0.85fr);
  max-width: 58rem;
  margin: 0 auto;
  border: 1px solid var(--line);
  background: var(--line);
  gap: 1px;
}

.subject-overview-inner > * {
  min-width: 0;
  background: var(--paper-bright);
  padding: clamp(1.4rem, 3vw, 2.5rem);
}

.subject-overview-inner > header {
  min-height: 20rem;
}

.subject-overview-inner h2 {
  max-width: 11ch;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3rem, 6vw, 5.6rem);
  font-weight: 500;
  letter-spacing: -0.06em;
  line-height: 0.92;
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
  font-weight: 720;
}

.subject-score-card {
  border-top: 4px solid var(--blue);
}

.subject-score-card :deep(.question-score strong) {
  font-size: clamp(4rem, 8vw, 7rem);
}

.subject-score-card > p {
  margin: 1.2rem 0 0;
  color: var(--muted);
  font-size: 0.75rem;
  line-height: 1.55;
}

.subject-facts {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
}

.subject-facts > div {
  padding: 1rem;
  border-right: 1px solid var(--line-soft);
}

.subject-facts > div:last-child {
  border-right: 0;
}

.subject-facts dt {
  color: var(--muted);
  font-size: 0.61rem;
  font-weight: 760;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subject-facts dd {
  margin: 0.45rem 0 0;
  font-family: var(--font-display);
  font-size: 1.7rem;
}

.subject-reliability {
  border-top: 4px solid var(--acid);
}

.subject-reliability.breached {
  border-top-color: var(--coral);
  background: #fff7f3;
}

.subject-reliability h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 500;
  letter-spacing: -0.04em;
}

.subject-reliability p:last-child,
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
</style>
