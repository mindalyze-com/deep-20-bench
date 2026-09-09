<script setup lang="ts">
import { editionsIndex } from "@/lib/api";
</script>
<template>
  <div id="route-content" class="content-section" tabindex="-1">
    <div class="content-inner">
      <h1>Benchmark edition unavailable</h1>
      <p>This link does not identify an available edition.</p>
      <div class="button-row">
        <RouterLink v-for="edition in editionsIndex?.editions ?? []" :key="edition.edition_id"
          class="button button-secondary" :to="{ name: 'home', params: { editionId: edition.edition_id } }">
          View edition {{ edition.label }}
        </RouterLink>
      </div>
    </div>
  </div>
</template>
