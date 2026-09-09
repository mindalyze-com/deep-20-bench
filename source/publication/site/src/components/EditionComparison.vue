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
  <section id="editions" class="content-section edition-comparison">
    <div class="content-inner">
      <p class="eyebrow">Benchmark editions</p>
      <h2>What changed in 1.1</h2>
      <p>Version 1.0 uses Yes, No, and Unknown for factual questions. Version 1.1 adds
        Rather yes and Rather no, so an answer can preserve a supported direction while
        acknowledging incomplete evidence.</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <table v-else>
        <caption class="visually-hidden">Comparison of published benchmark definitions</caption>
        <thead><tr><th scope="col">Setting</th><th v-for="document in documents" :key="document.edition_id" scope="col">Version {{ document.active_cohort.edition_label }}</th></tr></thead>
        <tbody>
          <tr><th scope="row">Question answers</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.eligibility.kind === 'qualified_release' ? 'Yes, Rather yes, Rather no, No, Unknown' : 'Yes, No, Unknown' }}</td></tr>
          <tr><th scope="row">Subjects</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.target_ids.length }}</td></tr>
          <tr><th scope="row">Rounds per subject</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.iterations }}</td></tr>
          <tr><th scope="row">Question limit</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.max_questions }}</td></tr>
          <tr><th scope="row">Failure score</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.max_questions + document.score_policy.failure_penalty_offset }}</td></tr>
          <tr><th scope="row">Review policy</th><td v-for="document in documents" :key="document.edition_id">{{ document.active_cohort.eligibility.kind === 'qualified_release' ? 'Evidence or knowledge under the recorded policy; every exact-token disagreement goes to the Judge' : 'Evidence first, with a limited stable-knowledge fallback' }}</td></tr>
          <tr><th scope="row">Guess validation</th><td v-for="document in documents" :key="document.edition_id">Yes, No, Unknown</td></tr>
        </tbody>
      </table>
      <div class="answer-rationale" aria-labelledby="qualified-answers-title">
        <h3 id="qualified-answers-title">Why add Rather yes and Rather no?</h3>
        <p>Web evidence can favor an answer without fully establishing the exact claim.
          With three answers, Unknown loses that useful direction, while a firm Yes or No
          can overstate what the evidence supports. The two additional answers make that
          gap explicit.</p>
        <dl class="answer-meanings">
          <div><dt>Rather yes</dt><dd>Relevant evidence favors the claim, but a material gap
            prevents a firm Yes.</dd></div>
          <div><dt>Rather no</dt><dd>Relevant evidence favors rejecting the claim, but a material
            gap prevents a firm No.</dd></div>
          <div><dt>Unknown</dt><dd>There is no reliable direction, or unresolved ambiguity or
            conflicting evidence changes the answer.</dd></div>
        </dl>
        <p>These labels express uncertainty about the exact claim. They are not numerical
          probabilities or a measure of how often a property applies. A failed search alone
          does not justify No or Rather no.</p>
        <p>The Guesser is instructed to use qualified answers as clues, keep alternatives
          possible, and check key assumptions with a different property before narrowing
          heavily. Every directional answer still receives blind review, and any exact-token
          disagreement goes to the Judge. Identity guesses still use only Yes, No, or Unknown.</p>
        <p>The aim is to retain useful partial evidence without treating it as certainty.
          Whether this improves gameplay needs evaluation; adding answer classes alone does
          not establish better accuracy.</p>
      </div>
      <p>Edition 1.1 also revises the question strategy instructions and adds a fixed guide to
        category meanings. Scores, uncertainty, costs, and efficiency are calculated within
        each edition. Both use the same subject-balanced question-score formula. Because
        subjects, trial counts, limits, and prompts also differ, a score difference across
        editions cannot isolate the effect of the new answers or establish model improvement.</p>
    </div>
  </section>
</template>
<style scoped>
.edition-comparison { background: var(--surface-raised); }
h2 { font-family: var(--font-display); font-size: clamp(2rem, 4vw, 3.2rem); font-weight: var(--font-weight-medium); }
p { color: var(--text-secondary); max-width: 55rem; }
.answer-rationale { max-width: 55rem; margin-block: 2rem; }
h3 { font-family: var(--font-display); font-size: clamp(1.5rem, 3vw, 2rem); font-weight: var(--font-weight-medium); }
.answer-meanings { margin-block: 1.5rem; }
.answer-meanings > div { display: grid; grid-template-columns: 7rem minmax(0, 1fr); gap: 1rem; padding-block: .85rem; border-bottom: var(--rule-default); }
dt { font-weight: var(--font-weight-semibold); }
dd { margin: 0; color: var(--text-secondary); }
table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-block: 1.5rem; font-size: var(--text-small); }
th, td { padding: .85rem 1rem .85rem 0; text-align: left; vertical-align: top; border-bottom: var(--rule-default); overflow-wrap: anywhere; }
th { font-weight: var(--font-weight-semibold); }
@media (max-width: 480px) { table { font-size: .75rem; } th, td { padding-right: .5rem; } .answer-meanings > div { grid-template-columns: 1fr; gap: .35rem; } }
</style>
