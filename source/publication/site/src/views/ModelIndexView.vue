<script setup lang="ts">
import { computed } from "vue";

import ErrorState from "@/components/ErrorState.vue";
import LoadingState from "@/components/LoadingState.vue";
import ModelName from "@/components/ModelName.vue";
import RankBadge from "@/components/RankBadge.vue";
import { getModelIndex, peekModelIndex } from "@/lib/api";
import { number } from "@/lib/format";
import { editionRoute, modelRoute } from "@/lib/route-location";
import { usePageRouteContext } from "@/lib/route-context";
import { useEditionContext } from "@/lib/use-edition-context";
import { useKeyedPublicationLoad } from "@/lib/use-keyed-publication-load";
import { modelView } from "@/router";

const { editionId, selectedEdition } = useEditionContext();
const { document, loading, error } = useKeyedPublicationLoad({
  parameters: (): [string] => [editionId.value],
  load: getModelIndex,
  initial: () => peekModelIndex(editionId.value),
  fallbackError: "The model list could not be loaded.",
});
const editionLabel = computed(() => selectedEdition.value?.label ?? editionId.value);
usePageRouteContext({
  title: "Models",
  description: "Every model with an official Deep20Bench result, with a link to its summary.",
});
</script>

<template>
  <div id="route-content" class="page model-index-page" tabindex="-1">
    <LoadingState v-if="loading && document === null" label="Loading models" />
    <ErrorState v-else-if="error && document === null" :message="error" />

    <template v-else-if="document !== null">
      <section class="page-hero site-boundary-shell">
        <div class="page-hero-inner site-boundary">
          <div>
            <p class="eyebrow">Models · Edition {{ editionLabel }}</p>
            <h1>Models tested in edition {{ editionLabel }}.</h1>
          </div>
          <div class="lede">
            <p>
              {{ document.models.length }} models have an official result in this edition.
              Each summary shows the model's results by subject and links to every round.
            </p>
            <p>
              For the ranked comparison, see the
              <RouterLink :to="editionRoute('results')">results overview</RouterLink>.
            </p>
          </div>
        </div>
      </section>

      <section class="content-section" aria-labelledby="model-list-title">
        <div class="content-inner">
          <h2 id="model-list-title" class="visually-hidden">All models, A to Z</h2>
          <div class="table-wrap">
            <table class="data-table model-index-table">
              <thead>
                <tr>
                  <th scope="col">Model</th>
                  <th scope="col" data-numeric>Rank</th>
                  <th scope="col" data-numeric>Question score</th>
                  <th scope="col" data-numeric>Rounds solved</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in document.models" :key="entry.slug">
                  <th scope="row">
                    <RouterLink
                      :to="modelRoute(entry.slug, editionId)"
                      @mouseenter="modelView.preload()"
                      @focus="modelView.preload()"
                    >
                      <ModelName :name="entry.model.display_name" compact />
                    </RouterLink>
                  </th>
                  <td data-numeric><RankBadge :rank="entry.rank" /></td>
                  <td data-numeric>{{ number(entry.question_score) }}</td>
                  <td data-numeric>{{ entry.successful }} of {{ entry.terminal_trials }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="model-index-note">Lower question scores are better.</p>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.model-index-note {
  margin-top: 0.75rem;
  color: var(--text-secondary);
  font-size: var(--text-small);
}
</style>
