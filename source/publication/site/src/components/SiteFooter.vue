<script setup lang="ts">
import { onMounted, ref } from "vue";

import PublicationTime from "@/components/PublicationTime.vue";
import { getManifest, peekManifest } from "@/lib/api";
import { citeAndReuseLinks, contributionLinks } from "@/lib/site-resources";

const publicationUpdatedAt = ref<string | null>(peekManifest()?.provenance.built_at ?? null);

onMounted(async () => {
  if (publicationUpdatedAt.value !== null) return;
  try {
    const manifest = await getManifest();
    publicationUpdatedAt.value = manifest.provenance.built_at;
  } catch {
    publicationUpdatedAt.value = null;
  }
});
</script>

<template>
  <footer class="site-footer site-boundary-shell" aria-label="Site footer">
    <div class="site-footer-inner site-boundary">
      <div class="site-footer-intro">
        <strong>Deep20Bench</strong>
        <p>A public record of a fixed Twenty Questions benchmark.</p>
        <p>
          The software is source-available under a dual-license model: PolyForm Noncommercial
          for noncommercial use, with separate commercial licenses available.
        </p>
      </div>

      <nav aria-label="Citation and licenses">
        <strong>Cite and reuse</strong>
        <a
          v-for="link in citeAndReuseLinks"
          :key="link.label"
          :href="link.href"
          target="_blank"
          rel="noreferrer"
        >{{ link.label }} ↗</a>
      </nav>

      <nav aria-label="Contact and contributions">
        <strong>Contribute</strong>
        <a
          v-for="link in contributionLinks"
          :key="link.label"
          :href="link.href"
          target="_blank"
          rel="noreferrer"
        >{{ link.label }} ↗</a>
      </nav>
    </div>

    <div
      v-if="publicationUpdatedAt !== null"
      class="site-footer-build site-boundary"
      aria-label="Build information"
    >
      <span>
        Publication updated
        <PublicationTime :value="publicationUpdatedAt" />
      </span>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  padding-block: clamp(2rem, 4vw, 3.5rem) 1.2rem;
  border-top: var(--rule-inverse);
  background: var(--surface-inverse);
  color: var(--text-inverse);
}

.site-footer-inner {
  display: grid;
  grid-template-columns: minmax(16rem, 1.35fr) minmax(12rem, 0.7fr) minmax(12rem, 0.7fr);
  gap: clamp(2rem, 6vw, 6rem);
}

.site-footer strong {
  font-size: var(--text-small);
}

.site-footer-intro > strong {
  font-family: var(--font-display);
  font-size: clamp(2rem, 3vw, 3rem);
  font-weight: var(--font-weight-medium);
}

.site-footer p {
  max-width: 27rem;
  margin: 0.8rem 0 0;
  color: var(--text-inverse-muted);
  line-height: 1.6;
}

.site-footer nav {
  display: grid;
  align-content: start;
  gap: 0.75rem;
}

.site-footer nav strong {
  margin-bottom: 0.2rem;
  color: var(--acid);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.site-footer a {
  width: fit-content;
  color: var(--text-inverse-muted);
  font-size: var(--text-small);
  white-space: nowrap;
}

.site-footer a:hover,
.site-footer a:focus-visible {
  color: var(--text-inverse);
}

.site-footer-build {
  display: flex;
  gap: 1rem 2rem;
  margin-top: clamp(2rem, 4vw, 3rem);
  padding-top: 1rem;
  border-top: var(--rule-inverse-subtle);
  color: var(--text-inverse-subtle);
  font-size: var(--text-caption);
}

.site-footer-build span {
  display: flex;
  gap: 0.35rem;
}

.site-footer-build time {
  font-variant-numeric: tabular-nums;
}

@media (max-width: 760px) {
  .site-footer-inner {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .site-footer-build,
  .site-footer-build span {
    flex-direction: column;
    gap: 0.25rem;
  }
}

@media (min-width: 761px) and (max-width: 900px) {
  .site-footer-inner {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 2rem;
  }

  .site-footer-intro {
    grid-column: 1 / -1;
  }
}
</style>
