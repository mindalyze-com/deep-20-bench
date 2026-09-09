import {
  createRouter,
  type RouteComponent,
  type Router,
  type RouterHistory,
  type RouteRecordRaw,
} from "vue-router";

import {
  editionsIndex,
  getEditions,
  getLeaderboard,
  getManifest,
  pendingEditionId,
  selectedEditionId,
} from "@/lib/api";
import { applyPageMetadata } from "@/lib/page-metadata";
import { applyStructuredData, homepageStructuredData } from "@/lib/structured-data";

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

const routes: RouteRecordRaw[] = [
  {
    path: "/publication-unavailable/", name: "publication-unavailable",
    component: () => import("@/views/PublicationUnavailableView.vue"),
    meta: { depth: 1, title: "Publication unavailable" },
  },
  {
    path: "/editions/:editionId/unavailable/", name: "edition-unavailable",
    component: () => import("@/views/EditionUnavailableView.vue"),
    meta: { depth: 1, title: "Edition unavailable" },
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
              title: "Episode",
              workspace: true,
              context: "Episode",
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
    meta: { depth: 1, nav: null, title: "Page not found" },
  },
];

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
  router.beforeEach(async to => {
    pendingEditionId.value = null;
    pendingEditionPath = null;
    if (["edition-unavailable", "publication-unavailable", "not-found"].includes(String(to.name))) return;
    try {
      const index = await getEditions();
      const id = editionForRoute(to);
      if (!index.editions.some(edition => edition.edition_id === id)) {
        return { name: "edition-unavailable", params: { editionId: id }, replace: true };
      }
      if (typeof to.params.editionId !== "string" && typeof to.params.executionId !== "string"
          && ["home", "results", "results-cost", "results-time", "results-efficiency",
            "results-reliability", "methodology", "about", "data"].includes(String(to.name))) {
        return { name: to.name, params: { editionId: id }, query: to.query, hash: to.hash, replace: true };
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
    if (to.name !== "home") {
      applyStructuredData([]);
      return;
    }
    const editionId = editionForRoute(to);
    // These public documents share the homepage loader's cache. A late response must
    // never restore another edition's markup after a subsequent navigation.
    void Promise.all([getManifest(editionId), getLeaderboard(editionId)])
      .then(([manifest, leaderboard]) => {
        if (version !== structuredDataVersion) return;
        applyStructuredData(homepageStructuredData(manifest, leaderboard, __DEEP20_CANONICAL_URL__));
      })
      .catch(() => {
        if (version === structuredDataVersion) applyStructuredData([]);
      });
  });
  router.onError(() => {
    pendingEditionId.value = null;
    pendingEditionPath = null;
  });
  return router;
};
