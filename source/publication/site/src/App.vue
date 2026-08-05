<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import DrilldownBar from "@/components/DrilldownBar.vue";
import SiteHeader from "@/components/SiteHeader.vue";
import {
  clearRouteContext,
  routeContext,
  setRouteContext,
  type RouteContext,
} from "@/lib/route-context";

const route = useRoute();
const router = useRouter();
const viewport = ref<HTMLElement | null>(null);
const scrollPositions = new Map<string, number>();
const contextCache = new Map<string, Omit<RouteContext, "version">>();
let scrollRestoreVersion = 0;

const usesDocumentScroll = (): boolean =>
  window.matchMedia("(max-width: 760px)").matches;

const readScrollTop = (element: HTMLElement): number =>
  usesDocumentScroll() ? window.scrollY : element.scrollTop;

const writeScrollTop = (element: HTMLElement, top: number): void => {
  if (usesDocumentScroll()) window.scrollTo({ top });
  else element.scrollTop = top;
};

const maximumScrollTop = (element: HTMLElement): number => {
  if (usesDocumentScroll()) {
    return Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
  }
  return Math.max(0, element.scrollHeight - element.clientHeight);
};

const focusRouteContent = async (): Promise<void> => {
  await nextTick();
  const target = document.getElementById("route-content");
  target?.focus({ preventScroll: true });
};

const restoreScroll = async (): Promise<void> => {
  const version = ++scrollRestoreVersion;
  await nextTick();
  if (version !== scrollRestoreVersion) return;
  const element = viewport.value;
  if (element === null) return;
  if (route.meta.workspace === true) {
    writeScrollTop(element, 0);
    return;
  }
  const hash = route.hash.slice(1);
  if (hash) {
    const target = document.getElementById(decodeURIComponent(hash));
    if (target !== null) {
      target.scrollIntoView({ block: "start" });
      return;
    }
  }
  const targetPosition = scrollPositions.get(route.path) ?? 0;
  const apply = (): void => {
    if (version !== scrollRestoreVersion) return;
    writeScrollTop(element, Math.min(targetPosition, maximumScrollTop(element)));
  };
  apply();
  window.setTimeout(apply, 70);
  window.setTimeout(apply, 220);
};

router.beforeEach((to, from) => {
  const element = viewport.value;
  if (element !== null && from.meta.workspace !== true) {
    scrollPositions.set(from.path, readScrollTop(element));
  }
  if (element !== null && to.meta.workspace === true) {
    writeScrollTop(element, 0);
    element.scrollLeft = 0;
  }
  if (from.path !== to.path && from.name !== undefined) {
    contextCache.set(from.path, {
      title: routeContext.title,
      description: routeContext.description,
      level: routeContext.level,
      position: routeContext.position,
      crumbs: [...routeContext.crumbs],
      previous: routeContext.previous,
      next: routeContext.next,
    });
    const cachedContext = contextCache.get(to.path);
    if (cachedContext === undefined) clearRouteContext();
    else setRouteContext(cachedContext);
  }
});

router.afterEach((to, from) => {
  if (from.name !== undefined && to.path !== from.path) {
    void focusRouteContent();
  }
  void restoreScroll();
});

const canonicalUrl = computed(
  () => new URL(route.path.replace(/^\//, ""), __DEEP20_CANONICAL_URL__).href,
);

watch(
  () => [routeContext.title, routeContext.description, routeContext.version] as const,
  ([title, description]) => {
    document.title = title === "Deep20Bench" ? title : `${title} · Deep20Bench`;
    const descriptionMeta = document.querySelector<HTMLMetaElement>(
      'meta[name="description"]',
    );
    descriptionMeta?.setAttribute("content", description);
    let canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (canonical === null) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.append(canonical);
    }
    canonical.href = canonicalUrl.value;
    void restoreScroll();
  },
);

onMounted(() => {
  void restoreScroll();
});
</script>

<template>
  <div
    class="app-shell"
    :class="{ 'app-shell--drilldown': Number(route.meta.depth ?? 0) >= 2 }"
  >
    <a class="skip-link" href="#main">
      Skip to content
    </a>
    <SiteHeader />
    <DrilldownBar v-if="Number(route.meta.depth ?? 0) >= 2" />
    <main
      id="main"
      ref="viewport"
      class="app-viewport"
      :class="{
        'app-viewport--workspace': route.meta.workspace === true,
        'app-viewport--results': route.meta.resultsWorkspace === true,
      }"
      tabindex="-1"
    >
      <RouterView v-slot="{ Component }">
        <KeepAlive :max="50">
          <component :is="Component" />
        </KeepAlive>
      </RouterView>
    </main>
  </div>
</template>
