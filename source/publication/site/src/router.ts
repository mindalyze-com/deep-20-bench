import {
  START_LOCATION,
  createRouter,
  type RouteComponent,
  type RouteLocationNormalized,
  type Router,
  type RouterHistory,
  type RouteRecordRaw,
} from "vue-router";

import {
  editionsIndex,
  getEditions,
  getLeaderboard,
  getManifest,
  getModel,
  getModelIndex,
  getRun,
  pendingEditionId,
  selectedEditionId,
} from "@/lib/api";
import { applyPageMetadata } from "@/lib/page-metadata";
import {
  applyStructuredData,
  pageStructuredData,
  type StructuredDataPage,
} from "@/lib/structured-data";

interface LazyView {
  (): Promise<{ default: RouteComponent }>;
  preload: () => void;
}

// Vue Router resolves a lazy route component before it commits the navigation, so the click
// stays silent until the module arrives. `preload` lets a parent view fetch it beforehand.
const lazyView = (loader: () => Promise<{ default: RouteComponent }>): LazyView =>
  Object.assign(loader, {
    preload: (): void => {
      void loader().catch(() => undefined);
    },
  });

export const benchmarkWorkspaceView = lazyView(
  () => import("@/views/workspace/BenchmarkWorkspaceView.vue"),
);
export const subjectWorkspaceView = lazyView(
  () => import("@/views/workspace/SubjectWorkspaceView.vue"),
);
export const episodeView = lazyView(() => import("@/views/EpisodeView.vue"));
export const modelView = lazyView(() => import("@/views/ModelView.vue"));

const routes: RouteRecordRaw[] = [
  {
    path: "/publication-unavailable/", name: "publication-unavailable",
    component: () => import("@/views/PublicationUnavailableView.vue"),
    meta: { depth: 1, title: "Publication unavailable", trackPageview: false },
  },
  {
    path: "/editions/:editionId/unavailable/", name: "edition-unavailable",
    component: () => import("@/views/EditionUnavailableView.vue"),
    meta: { depth: 1, title: "Edition unavailable", trackPageview: false },
  },
  {
    path: "/editions/:editionId?/",
    alias: "/",
    name: "home",
    component: () => import("@/views/HomeView.vue"),
    meta: { depth: 0, nav: "Overview", title: "Overview" },
  },
  {
    path: "/editions/:editionId?/results/",
    alias: "/results/",
    component: () => import("@/views/results/ResultsWorkspaceView.vue"),
    meta: {
      depth: 1,
      nav: "Results",
      title: "Results",
      context: "Official results",
    },
    children: [
      {
        path: "",
        name: "results",
        component: () => import("@/views/results/ResultsOverviewView.vue"),
        meta: { depth: 1, nav: "Results", title: "Results" },
      },
      {
        path: "cost/",
        name: "results-cost",
        component: () => import("@/views/results/ResultsCostView.vue"),
        meta: { depth: 1, nav: "Results", title: "Cost results" },
      },
      {
        path: "reliability/",
        name: "results-reliability",
        component: () => import("@/views/results/ResultsReliabilityView.vue"),
        meta: {
          depth: 1,
          nav: "Results",
          title: "Stability results",
        },
      },
      {
        path: "time/",
        name: "results-time",
        component: () => import("@/views/results/ResultsTimeView.vue"),
        meta: { depth: 1, nav: "Results", title: "Time results" },
      },
      {
        path: "efficiency/",
        name: "results-efficiency",
        component: () => import("@/views/results/ResultsEfficiencyView.vue"),
        meta: {
          depth: 1,
          nav: "Results",
          title: "Efficiency results",
        },
      },
    ],
  },
  {
    path: "/editions/:editionId?/why/",
    alias: "/why/",
    name: "why",
    component: () => import("@/views/WhyView.vue"),
    meta: { depth: 1, nav: "Why", title: "Why" },
  },
  {
    path: "/editions/:editionId?/methodology/",
    alias: "/methodology/",
    name: "methodology",
    component: () => import("@/views/MethodologyView.vue"),
    meta: { depth: 1, nav: "Method", title: "Method" },
  },
  {
    path: "/editions/:editionId?/about/",
    alias: ["/about/", "/story/"],
    name: "about",
    component: () => import("@/views/StoryView.vue"),
    meta: {
      canonicalPath: "/about/",
      depth: 1,
      nav: "About",
      title: "About",
    },
  },
  {
    path: "/editions/:editionId?/data/",
    alias: "/data/",
    name: "data",
    component: () => import("@/views/DataView.vue"),
    meta: { depth: 1, nav: "Data", title: "Data" },
  },
  {
    path: "/editions/:editionId?/models/",
    alias: "/models/",
    name: "models",
    component: () => import("@/views/ModelIndexView.vue"),
    meta: { depth: 1, nav: "Results", title: "Models" },
  },
  {
    path: "/editions/:editionId?/models/:slug/",
    alias: "/models/:slug/",
    name: "model",
    component: modelView,
    meta: { depth: 2, nav: "Results", title: "Model" },
  },
  {
    path: "/runs/:executionId/",
    name: "run",
    component: benchmarkWorkspaceView,
    meta: {
      depth: 2,
      nav: "Results",
      title: "Model run",
      workspace: true,
      context: "Run workspace",
    },
    children: [
      {
        path: "subjects/:targetId/",
        name: "subject",
        component: subjectWorkspaceView,
        meta: {
          depth: 3,
          nav: "Results",
          title: "Subject",
          workspace: true,
          context: "Subject workspace",
        },
        children: [
          {
            path: "episodes/:trialId/",
            name: "episode",
            component: episodeView,
            meta: {
              depth: 4,
              nav: "Results",
              title: "Round",
              workspace: true,
              context: "Round",
            },
          },
        ],
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("@/views/NotFoundView.vue"),
    meta: { depth: 1, nav: null, title: "Page not found", trackPageview: false },
  },
];

// Browser messages for a dynamic import whose module file is missing (Chromium, Firefox, Safari).
const isStaleModuleError = (error: unknown): boolean =>
  error instanceof Error
  && /dynamically imported module|Importing a module script failed/i.test(error.message);

const routeParam = (to: RouteLocationNormalized, name: string): string | null => {
  const value = to.params[name];
  return typeof value === "string" ? value : null;
};

/** Load the documents behind a page's JSON-LD, or return null for pages without it. */
const structuredDataPage = (
  to: RouteLocationNormalized,
  editionId: string,
): Promise<StructuredDataPage> | null => {
  const name = String(to.name);
  if (name === "home" || name === "data") {
    const kind = name;
    return Promise.all([getManifest(editionId), getLeaderboard(editionId)])
      .then(([manifest, leaderboard]) => ({ kind, manifest, leaderboard }));
  }
  if (name === "models") {
    return Promise.all([getManifest(editionId), getModelIndex(editionId)])
      .then(([manifest, index]) => ({ kind: "model-index", manifest, index }));
  }
  const slug = routeParam(to, "slug");
  if (name === "model" && slug !== null) {
    return Promise.all([getManifest(editionId), getModel(editionId, slug)])
      .then(([manifest, model]) => ({ kind: "model", manifest, model }));
  }
  const executionId = routeParam(to, "executionId");
  if (executionId === null || !["run", "subject", "episode"].includes(name)) return null;
  const targetId = routeParam(to, "targetId");
  const trialId = routeParam(to, "trialId");
  return Promise.all([getManifest(editionId), getRun(executionId)])
    .then(([manifest, run]): StructuredDataPage => {
      if (name === "episode" && targetId !== null && trialId !== null) {
        return { kind: "episode", manifest, run, targetId, trialId };
      }
      if (name === "subject" && targetId !== null) return { kind: "subject", manifest, run, targetId };
      return { kind: "run", manifest, run };
    });
};

export const createPublicationRouter = (history: RouterHistory): Router => {
  const router = createRouter({ history, routes });
  let pendingEditionPath: string | null = null;
  let structuredDataVersion = 0;
  const metadataByRoute = new Map(__DEEP20_ROUTE_METADATA__.map((entry) => [entry.route, entry]));
  const editionForRoute = (to: { params: Record<string, string | string[]> }): string => {
    if (typeof to.params.executionId === "string") {
      const owner = editionsIndex.value?.editions.find(edition =>
        edition.runs.some(run => run.execution_id === to.params.executionId));
      if (owner !== undefined) return owner.edition_id;
    }
    return typeof to.params.editionId === "string" ? to.params.editionId
      : editionsIndex.value?.default_edition_id ?? "1.0";
  };
  // Retired model slugs and replaced runs are static aliases of a stable model page.
  const modelAliasTarget = (path: string, name: string, slug: string | null) => {
    const metadata = metadataByRoute.get(path.replace(/^\/+|\/+$/g, ""));
    const target = metadata?.canonical_route.match(/^editions\/([^/]+)\/models\/([^/]+)$/);
    if (target === undefined || target === null) return null;
    const [, editionId, targetSlug] = target;
    if (name !== "run" && !(name === "model" && slug !== targetSlug)) return null;
    return { name: "model", params: { editionId, slug: targetSlug } };
  };
  router.beforeEach(async to => {
    pendingEditionId.value = null;
    pendingEditionPath = null;
    if (["edition-unavailable", "publication-unavailable", "not-found"].includes(String(to.name))) return;
    const alias = modelAliasTarget(to.path, String(to.name), routeParam(to, "slug"));
    if (alias !== null) return { ...alias, query: to.query, hash: to.hash, replace: true };
    try {
      const index = await getEditions();
      const id = editionForRoute(to);
      const edition = index.editions.find(candidate => candidate.edition_id === id);
      if (edition === undefined) {
        return { name: "edition-unavailable", params: { editionId: id }, replace: true };
      }
      // Unknown model slugs and run IDs are missing pages, not unavailable data.
      const slug = routeParam(to, "slug");
      const executionId = routeParam(to, "executionId");
      if ((to.name === "model" && slug !== null
          && !edition.models.some(model => model.slug === slug))
        || (executionId !== null
          && !index.editions.some(item => item.runs.some(run => run.execution_id === executionId)))) {
        return {
          name: "not-found",
          params: { pathMatch: to.path.split("/").filter(Boolean) },
          query: to.query,
          hash: to.hash,
          replace: true,
        };
      }
      if (typeof to.params.editionId !== "string" && typeof to.params.executionId !== "string"
          && ["home", "results", "results-cost", "results-time", "results-efficiency",
            "results-reliability", "why", "methodology", "about", "data", "models", "model",
          ].includes(String(to.name))) {
        return {
          name: to.name, params: { ...to.params, editionId: id }, query: to.query, hash: to.hash, replace: true,
        };
      }
      if (id !== selectedEditionId.value) {
        pendingEditionPath = to.fullPath;
        pendingEditionId.value = id;
      }
      await getManifest(id);
    } catch {
      return { name: "publication-unavailable", query: { retry: to.fullPath }, replace: true };
    }
  });
  router.afterEach((to, _from, failure) => {
    if (pendingEditionPath === to.fullPath) {
      pendingEditionId.value = null;
      pendingEditionPath = null;
    }
    if (failure) return;
    if (!["edition-unavailable", "publication-unavailable", "not-found"].includes(String(to.name))) {
      selectedEditionId.value = editionForRoute(to);
    }
    applyPageMetadata(
      metadataByRoute.get(to.path.replace(/^\/+|\/+$/g, "")),
      __DEEP20_CANONICAL_URL__,
    );
    if (typeof document === "undefined") return;
    const version = ++structuredDataVersion;
    const page = structuredDataPage(to, editionForRoute(to));
    if (page === null) {
      applyStructuredData([]);
      return;
    }
    // These public documents share the page loaders' cache. A late response must
    // never restore another page's markup after a subsequent navigation.
    void page
      .then((resolved) => {
        if (version !== structuredDataVersion) return;
        applyStructuredData(pageStructuredData(resolved, __DEEP20_CANONICAL_URL__));
      })
      .catch(() => {
        if (version === structuredDataVersion) applyStructuredData([]);
      });
  });
  router.onError((error: unknown, to: RouteLocationNormalized, from: RouteLocationNormalized) => {
    pendingEditionId.value = null;
    pendingEditionPath = null;
    // A new deployment replaces hashed route modules. A page loaded before it can no longer
    // fetch them, so the click would do nothing. Load the target as a full page instead.
    // The initial route is excluded so a genuinely missing module cannot cause a reload loop.
    if (typeof window !== "undefined" && from !== START_LOCATION && isStaleModuleError(error)) {
      window.location.assign(router.resolve(to).href);
    }
  });
  return router;
};
