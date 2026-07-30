<script setup lang="ts">
import { onActivated } from "vue";

import { illustrativeRound } from "@/lib/illustrative-round";
import { setRouteContext } from "@/lib/route-context";

const priorWork = [
  {
    year: "2018",
    kind: "Question strategy",
    title: "Learning-to-Ask: Knowledge Acquisition via 20 Questions",
    authors: "Yihong Chen et al. · KDD",
    description: "Learns question strategies for finding an entity and gathering knowledge.",
    href: "https://www.microsoft.com/en-us/research/publication/learning-to-ask-knowledge-acquisition-via-20-questions/",
    source: "Microsoft Research",
  },
  {
    year: "2022",
    kind: "World knowledge",
    title: "20Q: Overlap-Free World Knowledge Benchmark for Language Models",
    authors: "Maxime De Bruyn et al. · GEM",
    description: "Uses Twenty Questions to test world knowledge without train–test overlap.",
    href: "https://aclanthology.org/2022.gem-1.46/",
    source: "ACL Anthology",
  },
  {
    year: "2024",
    kind: "Planning benchmark",
    title: "The Entity-Deduction Arena",
    authors: "Yizhe Zhang, Jiarui Lu & Navdeep Jaitly · Apple · ACL",
    description: "Tests LLM planning and state tracking through a hidden-entity game.",
    href: "https://machinelearning.apple.com/research/parlor-game-arena",
    source: "Apple Machine Learning Research",
  },
  {
    year: "2025",
    kind: "Adaptive elicitation",
    title: "Adaptive Elicitation of Latent Information Using Natural Language",
    authors: "Jimmy Wang et al. · ICML",
    description: "Chooses natural-language questions by reducing uncertainty.",
    href: "https://openreview.net/forum?id=I7N6vtUChM",
    source: "OpenReview",
  },
  {
    year: "2025",
    kind: "Information gain",
    title: "BED-LLM: Intelligent Information Gathering with LLMs",
    authors: "Deepro Choudhury et al. · Apple · ICLR",
    description: "Uses expected information gain to choose questions.",
    href: "https://machinelearning.apple.com/research/bed-llm",
    source: "Apple Machine Learning Research",
  },
] as const;

const applyRouteContext = (): void => {
  setRouteContext({
    title: "Story",
    description: "The origin of Deep20Bench, its creators, and related work.",
    level: null,
    position: null,
    crumbs: [],
    previous: null,
    next: null,
  });
};

applyRouteContext();
onActivated(applyRouteContext);
</script>

<template>
  <div id="route-content" class="page story-page" tabindex="-1">
    <section class="story-hero">
      <div class="story-grid" aria-hidden="true"></div>
      <div class="hero-number" aria-hidden="true">20</div>
      <div class="hero-copy">
        <p class="eyebrow">Origin · prior work</p>
        <h1>A shared idea, built into a benchmark.</h1>
        <p>
          Patrick Heusser and Markus Tuor came up with Deep20Bench while playing Twenty Questions
          with the kids. Patrick then designed and built the benchmark.
        </p>
      </div>
      <a class="hero-jump" href="#origin">Origin ↓</a>
    </section>

    <section id="origin" class="content-section">
      <div class="content-inner story-section">
        <div class="story-index"><span>01</span><p class="eyebrow">Origin</p></div>
        <div>
          <h2>The game needs knowledge and a plan.</h2>
          <div class="origin-columns">
            <p>
              One person chooses a subject. The others ask yes-or-no questions. Each answer
              should narrow the options.
            </p>
            <p>
              Deep20Bench gives that task to an LLM and counts how many questions it needs to
              identify the subject.
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="round-section" aria-labelledby="round-title">
      <div class="content-inner">
        <header class="section-heading">
          <div>
            <p class="eyebrow">02 · Example</p>
            <h2 id="round-title">One answer at a time.</h2>
          </div>
          <p>Each YES, NO, or UNKNOWN should change the next question.</p>
        </header>
        <div class="round-board">
          <div class="round-heading">
            <span>Illustrative round</span>
            <span>04 / 20</span>
          </div>
          <div class="round-body">
            <ol aria-label="Illustrative Twenty Questions sequence">
              <li
                v-for="(turn, index) in illustrativeRound.turns"
                :key="turn.prompt"
                :class="{ final: turn.kind === 'guess' }"
              >
                <span>{{ String(index + 1).padStart(2, "0") }}</span>
                <p>{{ turn.prompt }}</p>
                <strong>{{ turn.answer }}</strong>
              </li>
            </ol>
            <div class="subject-orbit" aria-hidden="true">
              <span>Hidden subject</span>
              <strong>?</strong>
            </div>
          </div>
          <div class="round-footer">
            <span>World knowledge</span>
            <span>State tracking</span>
            <span>Question strategy</span>
          </div>
        </div>
        <p class="example-note">
          Example only. Published runs show their actual questions, answers, and evidence.
        </p>
      </div>
    </section>

    <section class="apple-spotlight">
      <div>
        <p class="eyebrow">03 · Closest prior work</p>
        <p class="apple-kicker">Apple Machine Learning Research · ACL 2024</p>
        <h2>The Entity-Deduction Arena</h2>
        <p>
          Yizhe Zhang, Jiarui Lu, and Navdeep Jaitly test multi-turn planning and state tracking
          through a hidden-entity game. They also study self-play.
        </p>
        <div class="button-row">
          <a
            class="button button-primary"
            href="https://machinelearning.apple.com/research/parlor-game-arena"
            target="_blank"
            rel="noreferrer"
            aria-label="Apple research page (opens in a new tab)"
          >
            Apple research page ↗
          </a>
          <a
            class="button button-secondary"
            href="https://aclanthology.org/2024.acl-long.82/"
            target="_blank"
            rel="noreferrer"
            aria-label="ACL paper (opens in a new tab)"
          >
            ACL paper ↗
          </a>
        </div>
      </div>
      <aside aria-label="How the projects relate">
        <div>
          <strong>Shared ground</strong>
          <p>Hidden entities, model questions, and a question limit.</p>
        </div>
        <div>
          <strong>Deep20Bench</strong>
          <p>Repeated trials, equal subject weight, Guesser isolation, and public run details.</p>
        </div>
      </aside>
    </section>

    <section class="content-section research-section" aria-labelledby="research-title">
      <div class="content-inner">
        <header class="section-heading">
          <div>
            <p class="eyebrow">Prior work</p>
            <h2 id="research-title">Related research.</h2>
          </div>
          <p>Deep20Bench was developed independently. These projects address related problems.</p>
        </header>
        <div class="work-list">
          <article
            v-for="work in priorWork"
            :key="work.title"
            :class="{ featured: work.year === '2024' }"
          >
            <span class="work-year">{{ work.year }}</span>
            <span class="work-kind">{{ work.kind }}</span>
            <div>
              <h3>{{ work.title }}</h3>
              <p class="work-authors">{{ work.authors }}</p>
              <p>{{ work.description }}</p>
            </div>
            <a
              :href="work.href"
              target="_blank"
              rel="noreferrer"
              :aria-label="`Read ${work.title} (opens in a new tab)`"
            >
              {{ work.source }} ↗
            </a>
          </article>
        </div>
      </div>
    </section>

    <section class="scope-section">
      <div>
        <p class="eyebrow">Scope</p>
        <h2>What Deep20Bench measures.</h2>
      </div>
      <div class="scope-list">
        <article>
          <span>01</span>
          <h3>Model as questioner</h3>
          <p>The model chooses each question. This tests knowledge and planning.</p>
        </article>
        <article>
          <span>02</span>
          <h3>Limited input</h3>
          <p>The Guesser sees a category, its actions, and final answer tokens.</p>
        </article>
        <article>
          <span>03</span>
          <h3>Public records</h3>
          <p>Scores link to runs, subjects, transcripts, evidence, and usage data.</p>
        </article>
      </div>
    </section>

    <section class="story-closing">
      <div>
        <p class="eyebrow">Next</p>
        <h2>Method and results.</h2>
      </div>
      <div>
        <p>Read the rules or inspect the current model runs.</p>
        <div class="button-row">
          <RouterLink class="button button-primary" :to="{ name: 'methodology' }">
            Method
          </RouterLink>
          <RouterLink class="button button-secondary" :to="{ name: 'results' }">
            Results
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.story-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  min-height: clamp(25rem, 48vh, 32rem);
  padding: clamp(4rem, 7vw, 6.5rem) max(var(--gutter), calc((100vw - var(--max)) / 2));
  overflow: hidden;
  background: var(--ink);
  color: white;
}

.story-grid {
  position: absolute;
  inset: 0;
  opacity: 0.075;
  background-image:
    linear-gradient(rgb(255 255 255 / 20%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(255 255 255 / 20%) 1px, transparent 1px);
  background-size: 88px 88px;
}

.hero-number {
  position: absolute;
  right: -0.05em;
  bottom: -0.32em;
  color: rgb(255 255 255 / 4%);
  font-size: clamp(15rem, 42vw, 42rem);
  font-weight: 850;
  letter-spacing: -0.12em;
}

.hero-copy,
.hero-jump {
  position: relative;
  z-index: 1;
}

.hero-copy {
  align-self: center;
  max-width: 56rem;
}

.hero-copy h1,
.story-section h2,
.apple-spotlight h2,
.scope-section h2,
.story-closing h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3.3rem, 5.5vw, 5.5rem);
  font-weight: 470;
  letter-spacing: -0.048em;
  line-height: 0.94;
}

.hero-copy > p:last-child {
  max-width: 44rem;
  color: rgb(255 255 255 / 66%);
  font-size: 0.9rem;
  line-height: 1.65;
}

.hero-jump {
  align-self: end;
  color: var(--acid);
  font-size: 0.78rem;
  font-weight: 750;
}

.story-section {
  display: grid;
  grid-template-columns: minmax(9rem, 0.35fr) minmax(0, 1fr);
  gap: clamp(2rem, 8vw, 8rem);
}

.story-index > span {
  color: var(--blue);
  font: 720 0.75rem ui-monospace, monospace;
}

.story-section h2 {
  max-width: 14ch;
  font-size: clamp(2.7rem, 4vw, 4rem);
}

.origin-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-top: 2rem;
  color: var(--muted);
  line-height: 1.7;
}

.round-section {
  padding: clamp(3.5rem, 7vw, 6.5rem) var(--gutter);
  background: #e8e5dc;
}

.round-board {
  border: 1px solid var(--ink);
  background: var(--paper-bright);
}

.round-heading,
.round-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  background: var(--ink);
  color: white;
  font-size: 0.66rem;
  font-weight: 760;
  text-transform: uppercase;
}

.round-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(14rem, 0.4fr);
}

.round-body ol {
  margin: 0;
  padding: 0;
  list-style: none;
}

.round-body li {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 1rem;
  align-items: center;
  min-height: 5.5rem;
  padding: 1rem;
  border-bottom: 1px solid var(--line);
}

.round-body li:last-child {
  border-bottom: 0;
}

.round-body li > span {
  color: var(--muted);
  font: 720 0.68rem ui-monospace, monospace;
}

.round-body li p {
  margin: 0;
}

.round-body li strong {
  color: var(--blue);
  font-size: 0.68rem;
}

.round-body li.final {
  background: var(--acid);
}

.subject-orbit {
  display: grid;
  border-left: 1px solid var(--ink);
  background: var(--blue);
  color: white;
  place-content: center;
  text-align: center;
}

.subject-orbit span {
  font-size: 0.65rem;
  text-transform: uppercase;
}

.subject-orbit strong {
  color: var(--acid);
  font-family: var(--font-display);
  font-size: 8rem;
  font-weight: 500;
  line-height: 1;
}

.round-footer {
  background: transparent;
  color: var(--muted);
  border-top: 1px solid var(--ink);
}

.example-note {
  color: var(--muted);
  font-size: 0.75rem;
}

.apple-spotlight,
.scope-section,
.story-closing {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(20rem, 0.65fr);
  gap: clamp(3rem, 8vw, 8rem);
  padding: clamp(3.8rem, 8vw, 7rem)
    max(var(--gutter), calc((100vw - var(--max)) / 2));
}

.apple-spotlight {
  background: linear-gradient(115deg, #5363ff 0%, #3f4df0 100%);
  color: white;
}

.apple-spotlight > div:first-child {
  max-width: 60rem;
}

.apple-spotlight h2 {
  max-width: 12ch;
}

.apple-kicker,
.apple-spotlight > div > p:last-of-type {
  color: white;
  line-height: 1.7;
}

.apple-spotlight aside {
  align-self: end;
  border: 1px solid rgb(255 255 255 / 30%);
}

.apple-spotlight aside div {
  padding: 1.2rem;
  border-bottom: 1px solid rgb(255 255 255 / 22%);
}

.apple-spotlight aside div:last-child {
  border-bottom: 0;
  background: var(--acid);
  color: var(--ink);
}

.apple-spotlight aside p {
  margin-bottom: 0;
  line-height: 1.55;
}

.work-list {
  border-top: 1px solid var(--ink);
}

.work-list article {
  display: grid;
  grid-template-columns: 5rem minmax(8rem, 0.35fr) minmax(0, 1fr) auto;
  gap: 1.5rem;
  align-items: center;
  padding: 1.3rem 0;
  border-bottom: 1px solid var(--line);
}

.work-list article.featured {
  margin-inline: -1rem;
  padding-inline: 1rem;
  background: var(--acid);
}

.work-year {
  color: var(--blue);
  font: 740 0.75rem ui-monospace, monospace;
}

.work-kind,
.work-authors {
  color: var(--muted);
  font-size: 0.7rem;
}

.work-list h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
}

.work-list p {
  margin: 0.35rem 0 0;
  color: var(--muted);
}

.work-list article > a {
  font-size: 0.72rem;
  font-weight: 750;
}

.scope-section {
  background: var(--acid);
}

.scope-section h2,
.story-closing h2 {
  max-width: 11ch;
  font-size: clamp(2.7rem, 4vw, 4rem);
}

.scope-list {
  border-top: 1px solid var(--ink);
}

.scope-list article {
  display: grid;
  grid-template-columns: auto minmax(9rem, 0.4fr) minmax(0, 1fr);
  gap: 1.2rem;
  padding: 1.15rem 0;
  border-bottom: 1px solid rgb(17 19 28 / 30%);
}

.scope-list span {
  color: var(--blue-ink);
  font: 720 0.68rem ui-monospace, monospace;
}

.scope-list h3,
.scope-list p {
  margin: 0;
}

.scope-list p {
  line-height: 1.55;
}

.story-closing {
  background: var(--ink);
  color: white;
}

.story-closing > div:last-child {
  align-self: end;
}

.story-closing > div:last-child > p {
  color: rgb(255 255 255 / 62%);
}

@media (max-width: 850px) {
  .story-section,
  .apple-spotlight,
  .scope-section,
  .story-closing,
  .round-body {
    grid-template-columns: 1fr;
  }

  .subject-orbit {
    min-height: 16rem;
    border-top: 1px solid var(--ink);
    border-left: 0;
  }

  .work-list article {
    grid-template-columns: auto 1fr;
  }

  .work-list article > div,
  .work-list article > a {
    grid-column: 2;
  }
}

@media (max-width: 560px) {
  .story-hero,
  .origin-columns {
    grid-template-columns: 1fr;
  }

  .hero-jump {
    margin-top: 3rem;
  }

  .round-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .scope-list article {
    grid-template-columns: auto 1fr;
  }

  .scope-list p {
    grid-column: 2;
  }
}
</style>
