import { onActivated, onDeactivated, reactive, ref } from "vue";
import type { RouteLocationRaw } from "vue-router";

export interface RouteCrumb {
  label: string;
  to?: RouteLocationRaw;
}

export interface RouteSibling {
  label: string;
  to: RouteLocationRaw;
}

export interface RouteContext {
  title: string;
  description: string;
  level: string | null;
  position: string | null;
  crumbs: RouteCrumb[];
  previous: RouteSibling | null;
  next: RouteSibling | null;
  version: number;
}

export interface PageRouteContext {
  title: string;
  description: string;
}

const defaultDescription =
  "Compare AI models in a public Twenty Questions LLM benchmark measuring question strategy, multi-turn reasoning, state tracking, reliability, cost, and runtime.";

const state = reactive<RouteContext>({
  title: "Deep20Bench",
  description: defaultDescription,
  level: null,
  position: null,
  crumbs: [],
  previous: null,
  next: null,
  version: 0,
});

export const routeContext: RouteContext = state;

export const clearRouteContext = (): void => {
  state.title = "Deep20Bench";
  state.description = defaultDescription;
  state.level = null;
  state.position = null;
  state.crumbs = [];
  state.previous = null;
  state.next = null;
};

export const setRouteContext = (
  context: Omit<RouteContext, "version">,
): void => {
  state.title = context.title;
  state.description = context.description;
  state.level = context.level;
  state.position = context.position;
  state.crumbs = context.crumbs;
  state.previous = context.previous;
  state.next = context.next;
  state.version += 1;
};

export const usePageRouteContext = (context: PageRouteContext): void => {
  const apply = (): void => {
    setRouteContext({
      ...context,
      level: null,
      position: null,
      crumbs: [],
      previous: null,
      next: null,
    });
  };

  apply();
  onActivated(apply);
};

export const useActiveRouteContext = (apply: () => void): (() => void) => {
  const active = ref(true);
  onActivated(() => {
    active.value = true;
    apply();
  });
  onDeactivated(() => {
    active.value = false;
  });
  apply();
  return (): void => {
    if (active.value) apply();
  };
};
