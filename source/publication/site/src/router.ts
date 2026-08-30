import {
  createRouter,
  type RouteComponent,
  type Router,
  type RouterHistory,
  type RouteRecordRaw,
} from "vue-router";

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
    path: "/",
    name: "home",
    component: () => import("@/views/HomeView.vue"),
    meta: { depth: 0, nav: "Overview", title: "Overview" },
  },
  {
    path: "/results/",
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
    path: "/methodology/",
    name: "methodology",
    component: () => import("@/views/MethodologyView.vue"),
    meta: { depth: 1, nav: "Method", title: "Method" },
  },
  {
    path: "/about/",
    alias: "/story/",
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
    path: "/data/",
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
  router.afterEach((to) => {
    if (typeof document === "undefined") return;
    const title = typeof to.meta.title === "string" ? to.meta.title : "Deep20Bench";
    document.title = title === "Overview" ? "Deep20Bench" : `${title} · Deep20Bench`;
  });
  return router;
};
