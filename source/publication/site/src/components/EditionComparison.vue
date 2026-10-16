<script setup lang="ts">
import { ref } from "vue";
import { editionsIndex, getManifest, peekManifest } from "@/lib/api";
import { usePublicationLoad } from "@/lib/use-publication-load";
import type { ManifestDocument } from "@/lib/types";
const editions = editionsIndex.value?.editions ?? [];
const initial = editions.map(edition => peekManifest(edition.edition_id));
const documents = ref(initial.filter((item): item is ManifestDocument => item !== null));
const { error } = usePublicationLoad(async () => {
  documents.value = await Promise.all(editions.map(edition => getManifest(edition.edition_id)));
}, "Edition definitions could not be loaded.", documents.value.length === editions.length);
</script>
<template>
  <section id="edition-history" class="content-section edition-comparison" aria-label="Edition history">
    <div class="content-inner">
      <details class="disclosure edition-comparison-details">
        <summary>
          <span>
            <strong>What changed between editions?</strong>
            <small>Compare editions 1.0 and 1.1</small>
          </span>
          <span aria-hidden="true">
            <span class="comparison-open-label">View ↓</span>
            <span class="comparison-close-label">Hide ↑</span>
          </span>
        </summary>
        <div id="editions" class="edition-comparison-body">
          <p class="eyebrow">Benchmark editions</p>
          <h2>What changed in 1.1</h2>
          <p>In edition 1.0, questions get Yes, No, or Unknown. Edition 1.1 adds Rather yes and
            Rather no, so an answer can lean one way when the evidence is incomplete.</p>
          <p v-if="error" role="alert">{{ error }}</p>
          <table v-else>
            <caption class="visually-hidden">Comparison of published benchmark definitions</caption>
            <thead><tr><th scope="col">Setting</th><th v-for="document in documents" :key="document.edition_id" scope="col">Edition {{ document.active_cohort.edition_label }}</th></tr></thead>
            <tbody>
              <tr><th scope="row">Question answers</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.eligibility.kind === 'qualified_release' ? 'Yes, Rather yes, Rather no, No, Unknown' : 'Yes, No, Unknown' }}</td></tr>
              <tr><th scope="row">Subjects</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.target_ids.length }}</td></tr>
              <tr><th scope="row">Rounds per subject</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.iterations }}</td></tr>
              <tr><th scope="row">Question limit</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.max_questions }}</td></tr>
              <tr><th scope="row">Failure score</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.max_questions + document.score_policy.failure_penalty_offset }}</td></tr>
              <tr><th scope="row">Review rules</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.eligibility.kind === 'qualified_release' ? 'Evidence or model knowledge, as each run records; any disagreement goes to the Judge' : 'Evidence first; model knowledge only for settled facts' }}</td></tr>
              <tr><th scope="row">Guess validation</th><td v-for="document in documents" :key="document.edition_id">Yes, No, Unknown</td></tr>
            </tbody>
          </table>
          <div class="answer-rationale" aria-labelledby="qualified-answers-title">
            <h3 id="qualified-answers-title">Why add Rather yes and Rather no?</h3>
            <p>Web evidence often points one way without fully proving the claim. With only
              three answers, Unknown throws that hint away, while a firm Yes or No can claim
              more than the evidence shows. The two new answers keep the hint and mark it as
              uncertain. Whether this improves the game still needs testing.</p>
          </div>
          <p>Edition 1.1 also revises the Guesser's strategy instructions and adds a fixed guide
            to what each category means. Both editions use the same scoring formula, but results
            are calculated separately. Because the subjects, round counts, limits, and prompts
            differ, a score difference between editions does not show the effect of the new
            answers or that a model improved.</p>
        </div>
      </details>
    </div>
  </section>
</template>
<style scoped>
.edition-comparison {
  padding-block: clamp(1.5rem, 3vw, 2.5rem);
  background: var(--surface-raised);
}
.edition-comparison-body {
  padding: 0 clamp(1rem, 3vw, 2rem) clamp(1rem, 3vw, 2rem);
  scroll-margin-top: 1.5rem;
}
.comparison-close-label { display: none; }
.edition-comparison-details[open] .comparison-open-label { display: none; }
.edition-comparison-details[open] .comparison-close-label { display: inline; }
h2 { font-family: var(--font-display); font-size: clamp(2rem, 4vw, 3.2rem); font-weight: var(--font-weight-medium); }
p { color: var(--text-secondary); max-width: 55rem; }
.answer-rationale { max-width: 55rem; margin-block: 2rem; }
h3 { font-family: var(--font-display); font-size: clamp(1.5rem, 3vw, 2rem); font-weight: var(--font-weight-medium); }
table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-block: 1.5rem; font-size: var(--text-small); }
th, td { padding: .85rem 1rem .85rem 0; text-align: left; vertical-align: top; border-bottom: var(--rule-default); overflow-wrap: anywhere; }
th { font-weight: var(--font-weight-semibold); }
@media (max-width: 480px) { table { font-size: .75rem; } th, td { padding-right: .5rem; } }
</style>
