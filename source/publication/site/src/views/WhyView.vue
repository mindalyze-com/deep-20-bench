<script setup lang="ts">
import { editionRoute } from "@/lib/route-location";
import { usePageRouteContext } from "@/lib/route-context";

usePageRouteContext({
  title: "Why",
  description: "Why Twenty Questions makes a simple, repeatable test for AI models.",
});
</script>

<template>
  <div id="route-content" class="page why-page" tabindex="-1">
    <section class="page-hero site-boundary-shell">
      <div class="page-hero-inner site-boundary">
        <div>
          <p class="eyebrow">Why Deep20Bench</p>
          <h1>Easy to play, hard to play well.</h1>
        </div>
        <p class="lede">
          Anyone can play Twenty Questions. Playing it with few questions is hard. That makes it
          a simple, repeatable test of how well AI models use what they know.
        </p>
      </div>
    </section>

    <section id="reasons" class="content-section reasons-section">
      <div class="content-inner editorial-copy">
        <div><p class="eyebrow">01 · What it tests</p></div>
        <div>
          <h2>Why the game works as a test.</h2>
          <ol class="numbered-points">
            <li><h3>The game is uneven.</h3>
              <p>The Oracle knows the subject and only checks one fact per question. The
                Guesser starts with almost nothing and must search a huge space. Checking one
                fact about a known subject is far easier than finding a good question
                without knowing it. Answer mistakes still happen, so answers get a second check.</p></li>
            <li><h3>Each question must build on the last.</h3>
              <p>The first questions are easy: real or fictional, alive or dead. After that,
                broad questions stop helping. The best next question uses every earlier answer
                and splits the remaining possibilities roughly in half. Twenty perfect splits
                can separate about a million possibilities (2<sup>20</sup>).</p></li>
            <li><h3>Knowledge alone is not enough.</h3>
              <p>Recognizing Albert Einstein in a photo is easy. Finding him with only Yes and
                No answers is not. There is no universal list of questions: after a good
                opening, the right question depends on what the model knows about the
                candidates that are left.</p></li>
            <li><h3>Simple, repeatable, and extendable.</h3>
              <p>The result is one number, the questions needed, measured the same way for
                every model. Adding a subject to the catalog takes only a name, a description,
                and a public reference; testing it still takes repeated rounds and answer
                checks. New editions can use new subjects.</p></li>
            <li><h3>It also tests discipline.</h3>
              <p>Every reply must follow a fixed format for dozens of turns. Some models follow
                it for ten turns, break it once, and recover after one reminder. Others forget
                the rules in the middle of a game. Before the question limit, each broken
                reply costs a turn.</p></li>
          </ol>
        </div>
      </div>
    </section>

    <section id="limits" class="content-section limits-section">
      <div class="content-inner editorial-copy">
        <div><p class="eyebrow">02 · Limits</p></div>
        <div>
          <h2>What it does not show.</h2>
          <p>
            The game measures a narrow mix of skills: world knowledge, planning, using earlier
            answers, and following rules. It is not a measure of general intelligence. Each
            edition uses a small, fixed set of subjects, and other models check the answers,
            so mistakes are possible. The subjects and transcripts are public, so a later model
            may have seen them in training; an advantage from training data cannot be ruled out.
          </p>
          <p>
            See <RouterLink :to="editionRoute('methodology', { hash: '#answer-checks' })">how
              answers are checked</RouterLink> and
            <RouterLink :to="editionRoute('methodology', { hash: '#repetition' })">what a
              comparison can tell you</RouterLink>.
          </p>
        </div>
      </div>
    </section>

    <section id="related-work" class="content-section related-section">
      <div class="content-inner editorial-copy">
        <div><p class="eyebrow">03 · Related work</p></div>
        <div>
          <h2>Not a new idea.</h2>
          <p>
            Researchers at Microsoft and Apple have used Twenty Questions to study how AI asks
            questions and plans a search. Deep20Bench builds on the same idea as a public
            leaderboard: current models, repeated rounds, and every game published.
          </p>
          <p>
            See <RouterLink :to="editionRoute('about', { hash: '#research' })">related
              research</RouterLink>.
          </p>
        </div>
      </div>
    </section>

    <section class="why-closing site-boundary-shell">
      <nav class="why-closing-inner site-boundary" aria-label="Continue from Why">
        <div>
          <p class="eyebrow">Next</p>
          <h2>See how it works.</h2>
        </div>
        <div class="button-row">
          <RouterLink class="button button-primary" :to="editionRoute('methodology')">
            How it works →
          </RouterLink>
          <RouterLink class="button button-secondary" :to="editionRoute('results')">
            Results
          </RouterLink>
        </div>
      </nav>
    </section>
  </div>
</template>

<style scoped>
.page-hero h1 {
  max-width: 14ch;
  font-size: clamp(2.75rem, 5vw, 5rem);
}

.editorial-copy h2 {
  max-width: 22ch;
}

.editorial-copy h3 {
  font-family: var(--font-display);
  font-weight: var(--font-weight-medium);
}

.reasons-section,
.related-section {
  background: var(--paper-bright);
}

.numbered-points {
  margin-block: 1.5rem 0;
  padding-left: 1.5rem;
}

.numbered-points li {
  padding: 0.75rem 0 0.75rem 0.5rem;
  border-bottom: var(--rule-default);
}

.numbered-points li::marker {
  color: var(--blue-ink);
  font-weight: var(--font-weight-semibold);
}

.numbered-points h3 {
  margin: 0 0 0.4rem;
  font-size: 1.25rem;
}

.numbered-points p {
  margin: 0;
}

.why-closing {
  padding-block: clamp(2.5rem, 5vw, 4rem);
  background: var(--surface-rail);
}

.why-closing-inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: start;
  gap: 1.25rem 2rem;
}

.why-closing h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-section-title);
  font-weight: var(--font-weight-medium);
  letter-spacing: -0.042em;
}

.why-closing .button-row {
  margin: 0;
}
</style>
