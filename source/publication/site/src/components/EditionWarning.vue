<script setup lang="ts">
import { useRoute } from "vue-router";
import { pendingEditionId } from "@/lib/api";
import { editionRoute } from "@/lib/route-location";
import { editionDestination, useEditionContext } from "@/lib/use-edition-context";

const route = useRoute();
const { selectedEdition, currentEdition, isPreviousEdition } = useEditionContext();
const preventPendingNavigation = (event: MouseEvent): void => {
  if (pendingEditionId.value !== null) event.preventDefault();
};
</script>

<template>
  <div role="status" aria-atomic="true">
    <aside v-if="isPreviousEdition && selectedEdition && currentEdition"
      class="edition-warning site-boundary-shell" aria-label="Previous edition">
      <div class="edition-warning-inner site-boundary">
        <span class="edition-warning-icon" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 10a9 9 0 1 1 2.6 8.4M3 4v6h6M12 7v5l3 2" />
          </svg>
        </span>
        <p class="edition-warning-copy">You're viewing a previous edition (v.{{ selectedEdition.edition_id }}).</p>
        <div class="edition-warning-actions">
          <RouterLink class="edition-warning-upgrade" :to="editionDestination(route, currentEdition)"
            :aria-disabled="pendingEditionId !== null ? 'true' : undefined"
            @click.capture="preventPendingNavigation">
            <span>View latest <span class="edition-warning-version">(v.{{ currentEdition.edition_id }})</span></span>
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none"
              stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 8h10M9 4l4 4-4 4" />
            </svg>
          </RouterLink>
          <RouterLink class="edition-warning-details"
            :to="editionRoute('methodology', { editionId: currentEdition.edition_id, hash: '#editions' })"
            :aria-disabled="pendingEditionId !== null ? 'true' : undefined"
            @click.capture="preventPendingNavigation">What changed</RouterLink>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.edition-warning { background: var(--surface-inverse); color: var(--text-inverse-muted); border-bottom: var(--rule-inverse-subtle); }
.edition-warning-inner { display: flex; align-items: center; gap: .65rem; }
.edition-warning-icon { display: flex; flex-shrink: 0; color: var(--acid); }
.edition-warning-copy { flex: 1; margin: 0; font-size: var(--text-caption); line-height: 1.5; }
.edition-warning-actions { display: flex; align-items: center; gap: 1rem; flex-shrink: 0; }
.edition-warning-actions a { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; font-size: var(--text-caption); }
.edition-warning-upgrade { gap: .4rem; color: var(--acid); text-decoration: none; text-underline-offset: .2em; }
.edition-warning-upgrade:hover { text-decoration: underline; }
.edition-warning-version { white-space: nowrap; }
.edition-warning-details { color: var(--text-inverse-muted); text-underline-offset: .2em; }
.edition-warning-details:hover { color: var(--text-inverse); }
.edition-warning-actions a:focus-visible { outline-color: var(--acid); }
.edition-warning-actions a[aria-disabled] { opacity: .6; cursor: progress; }
@media (max-width: 700px) {
  .edition-warning-inner { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 0 .5rem; padding-top: .6rem; }
  .edition-warning-actions { grid-column: 2; flex-wrap: wrap; gap: 0 1rem; }
}
</style>
