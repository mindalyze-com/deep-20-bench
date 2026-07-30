import { reactive } from "vue";
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

const defaultDescription =
  "Tests how LLMs use world knowledge, question planning, and state tracking to identify a hidden subject.";

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
