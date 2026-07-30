<template>
  <footer class="site-footer">
    <div>
      <p class="eyebrow">Deep20Bench</p>
      <p class="footer-statement">Can an LLM ask its way to the answer?</p>
    </div>
    <nav class="footer-links" aria-label="Footer navigation">
      <RouterLink :to="{ name: 'results' }">Results</RouterLink>
      <RouterLink :to="{ name: 'methodology' }">Method</RouterLink>
      <RouterLink :to="{ name: 'story' }">Story &amp; prior work</RouterLink>
      <RouterLink :to="{ name: 'data' }">Data</RouterLink>
      <a
        href="https://github.com/mindalyze-com/deep-20-bench"
        target="_blank"
        rel="noreferrer"
      >
        Source code ↗ <span class="visually-hidden">(opens in a new tab)</span>
      </a>
    </nav>
    <p class="footer-fineprint">
      Patrick Heusser and Markus Tuor developed the idea together. Patrick designed and built
      Deep20Bench. This static site is generated from completed run files and makes no model
      calls.
    </p>
  </footer>
</template>
