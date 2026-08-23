<script setup lang="ts">
import { onActivated } from "vue";

import { setRouteContext } from "@/lib/route-context";

const newsEntries = [
  {
    date: "2026-08-23",
    displayDate: "23 August 2026",
    title: "OpenRouter’s Ox Alpha (high) tested.",
    summary:
      "The Stealth-routed model won 32 of 35 trials and scored 17.6 questions, placing 12th of 15.",
    executionId: "BX-20260823-official-M0017-018",
  },
  {
    date: "2026-08-17",
    displayDate: "17 August 2026",
    title: "Gemini 3.7 Flash (high) added.",
    summary: "It scored 14.0 questions with 34 of 35 successful trials.",
    executionId: "BX-20260817-official-M0016-015",
  },
  {
    date: "2026-08-15",
    displayDate: "15 August 2026",
    title: "Grok 4.6 (high) added.",
    summary: "It scored 14.3 questions with 35 of 35 successful trials.",
    executionId: "BX-20260814-official-M0015-013",
  },
  {
    date: "2026-08-05",
    displayDate: "5 August 2026",
    title: "Claude Fable 5 (high) added.",
    summary: "We added Claude Fable 5 (high) to the official Deep20Bench results.",
    executionId: "BX-20260805-official-M0014-011",
  },
] as const;

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
    title: "About",
    description: "The origin of Deep20Bench, project news, and related work.",
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
    <section class="story-hero site-boundary-shell">
      <div class="story-grid" aria-hidden="true"></div>
      <div class="hero-number" aria-hidden="true">20</div>
      <div class="story-hero-inner site-boundary">
        <div class="hero-copy">
          <p class="eyebrow">Origin · news · prior work</p>
          <h1>A shared idea, built into a benchmark.</h1>
          <p>
            Patrick Heusser and Markus Tuor came up with Deep20Bench while playing Twenty Questions
            with the kids. Patrick then designed and built the benchmark.
          </p>
        </div>
        <a class="hero-jump" href="#news">Latest news ↓</a>
      </div>
    </section>

    <section id="news" class="content-section news-section" aria-labelledby="news-title">
      <div class="content-inner">
        <header class="section-heading">
          <div>
            <p class="eyebrow">Updates</p>
            <h2 id="news-title">Project news.</h2>
          </div>
          <p>Dated changes to the official publication.</p>
        </header>
        <div class="news-list">
          <article
            v-for="entry in newsEntries"
            :key="entry.executionId"
            class="news-entry"
          >
            <time :datetime="entry.date">{{ entry.displayDate }}</time>
            <div>
              <h3>{{ entry.title }}</h3>
              <p>{{ entry.summary }}</p>
            </div>
            <RouterLink
              class="news-link"
              :to="{
                name: 'run',
                params: { executionId: entry.executionId },
              }"
            >
              View run →
            </RouterLink>
          </article>
        </div>
      </div>
    </section>

    <section id="research" class="content-section research-section" aria-labelledby="research-title">
      <div class="content-inner">
        <header class="section-heading">
          <div>
            <p class="eyebrow">Prior work</p>
            <h2 id="research-title">Related research.</h2>
          </div>
          <p>Deep20Bench was developed independently. These projects address related problems.</p>
        </header>
        <table class="work-table">
          <caption>
            Research related to Deep20Bench
          </caption>
          <colgroup>
            <col class="work-col-year" />
            <col class="work-col-kind" />
            <col />
            <col class="work-col-source" />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">Focus</th>
              <th scope="col">Publication</th>
              <th scope="col">Source</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="work in priorWork"
              :key="work.title"
            >
              <td class="work-year">{{ work.year }}</td>
              <td class="work-kind">{{ work.kind }}</td>
              <td class="work-details">
                <h3>{{ work.title }}</h3>
                <p class="work-authors">{{ work.authors }}</p>
                <p>{{ work.description }}</p>
              </td>
              <td class="work-source">
                <a
                  :href="work.href"
                  target="_blank"
                  rel="noreferrer"
                  :aria-label="`Read ${work.title} (opens in a new tab)`"
                >
                  {{ work.source }} ↗
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="story-closing site-boundary-shell">
      <div class="story-closing-inner site-boundary">
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
      </div>
    </section>
  </div>
</template>

<style scoped>
.story-hero {
  position: relative;
  min-height: clamp(25rem, 48vh, 32rem);
  padding-block: clamp(4rem, 7vw, 6.5rem);
  overflow: hidden;
  background: var(--ink);
  color: white;
}

.story-hero-inner {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  min-height: calc(clamp(25rem, 48vh, 32rem) - 2 * clamp(4rem, 7vw, 6.5rem));
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
  right: max(var(--gutter), calc((100vw - var(--max)) / 2));
  bottom: -0.32em;
  color: rgb(255 255 255 / 4%);
  font-size: clamp(15rem, 42vw, 42rem);
  font-weight: var(--font-weight-extrabold);
  letter-spacing: -0.12em;
}

.hero-copy,
.hero-jump {
  position: relative;
}

.hero-copy {
  align-self: center;
  max-width: 56rem;
}

.hero-copy h1,
.news-section h2,
.story-closing h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(3.3rem, 5.5vw, 5.5rem);
  font-weight: var(--font-weight-medium);
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
  font-size: var(--text-small);
  font-weight: var(--font-weight-bold);
}

.news-section {
  background: var(--surface-rail);
}

.news-list {
  display: grid;
  gap: 1rem;
}

.news-entry {
  display: grid;
  grid-template-columns: minmax(9rem, 0.25fr) minmax(0, 1fr) auto;
  gap: clamp(1.5rem, 4vw, 4rem);
  align-items: center;
  padding: clamp(1.5rem, 3vw, 2.5rem);
  border: var(--rule-strong);
  background: var(--acid);
}

.news-entry time {
  color: var(--blue-ink);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.news-entry h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(1.65rem, 3vw, 2.4rem);
  font-weight: var(--font-weight-medium);
}

.news-entry p {
  margin: 0.4rem 0 0;
  line-height: 1.55;
}

.story-closing {
  padding-block: clamp(3.8rem, 8vw, 7rem);
  background: var(--ink);
  color: white;
}

.story-closing-inner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(20rem, 0.65fr);
  gap: clamp(3rem, 8vw, 8rem);
}

.work-table {
  width: 100%;
  border-top: var(--rule-strong);
  border-collapse: collapse;
  table-layout: fixed;
}

.work-table caption {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.work-col-year {
  width: 8rem;
}

.work-col-kind {
  width: 7rem;
}

.work-col-source {
  width: 18rem;
}

.work-table th {
  padding: 0.75rem 1.5rem 0.75rem 0;
  border-bottom: var(--rule-strong);
  color: var(--muted);
  font-size: var(--text-micro);
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.08em;
  text-align: left;
  text-transform: uppercase;
}

.work-table th:last-child,
.work-table td:last-child {
  padding-right: 0;
  text-align: right;
}

.work-table td {
  padding: 1.3rem 1.5rem 1.3rem 0;
  border-bottom: var(--rule-default);
  vertical-align: middle;
}

.work-year {
  color: var(--blue);
  font: var(--font-weight-bold) var(--text-small) var(--font-mono);
}

.work-kind,
.work-authors {
  color: var(--muted);
  font-size: var(--text-small);
}

.work-kind {
  line-height: 1.35;
}

.work-table h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: var(--font-weight-medium);
}

.work-table p {
  margin: 0.35rem 0 0;
  color: var(--muted);
}

.work-source a {
  font-size: var(--text-small);
  font-weight: var(--font-weight-bold);
}

.story-closing h2 {
  max-width: 11ch;
  font-size: clamp(2.7rem, 4vw, 4rem);
}

.story-closing-inner > div:last-child {
  align-self: end;
}

.story-closing-inner > div:last-child > p {
  color: rgb(255 255 255 / 62%);
}

@media (max-width: 850px) {
  .story-closing-inner {
    grid-template-columns: 1fr;
  }

  .news-entry {
    grid-template-columns: 1fr auto;
  }

  .news-entry > div {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .work-table {
    display: block;
    border-collapse: separate;
    table-layout: auto;
  }

  .work-table colgroup,
  .work-table thead {
    display: none;
  }

  .work-table tbody {
    display: block;
  }

  .work-table tr {
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: 1.25rem;
    padding: 1.3rem 0;
    border-bottom: var(--rule-default);
  }

  .work-table td {
    display: block;
    padding: 0;
    border: 0;
  }

  .work-year {
    grid-row: 1 / 4;
  }

  .work-kind,
  .work-details,
  .work-source {
    grid-column: 2;
  }

  .work-details {
    margin-top: 0.7rem;
  }

  .work-table td:last-child {
    margin-top: 0.75rem;
    text-align: left;
  }
}

@media (max-width: 560px) {
  .story-hero-inner {
    grid-template-columns: 1fr;
  }

  .hero-jump {
    margin-top: 3rem;
  }

  .news-entry {
    grid-template-columns: 1fr;
  }

  .news-entry > div,
  .news-link {
    grid-column: 1;
  }
}
</style>
