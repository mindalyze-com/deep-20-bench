import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

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
      workspace: true,
      resultsWorkspace: true,
      context: "Official results",
    },
    children: [
      {
        path: "",
        name: "results",
        component: () => import("@/views/results/ResultsOverviewView.vue"),
        meta: { depth: 1, nav: "Results", title: "Results", workspace: true },
      },
      {
        path: "cost/",
        name: "results-cost",
        component: () => import("@/views/results/ResultsCostView.vue"),
        meta: { depth: 1, nav: "Results", title: "Cost results", workspace: true },
      },
      {
        path: "reliability/",
        name: "results-reliability",
        component: () => import("@/views/results/ResultsReliabilityView.vue"),
        meta: {
          depth: 1,
          nav: "Results",
          title: "Stability results",
          workspace: true,
        },
      },
      {
        path: "time/",
        name: "results-time",
        component: () => import("@/views/results/ResultsTimeView.vue"),
        meta: { depth: 1, nav: "Results", title: "Time results", workspace: true },
      },
      {
        path: "efficiency/",
        name: "results-efficiency",
        component: () => import("@/views/results/ResultsEfficiencyView.vue"),
        meta: {
          depth: 1,
          nav: "Results",
          title: "Efficiency results",
          workspace: true,
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
    path: "/story/",
    name: "story",
    component: () => import("@/views/StoryView.vue"),
    meta: { depth: 1, nav: "Story", title: "Story" },
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
    component: () => import("@/views/workspace/BenchmarkWorkspaceView.vue"),
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
        component: () => import("@/views/workspace/SubjectWorkspaceView.vue"),
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
            component: () => import("@/views/EpisodeView.vue"),
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

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.afterEach((to) => {
  const title = typeof to.meta.title === "string" ? to.meta.title : "Deep20Bench";
  document.title = title === "Overview" ? "Deep20Bench" : `${title} · Deep20Bench`;
});
