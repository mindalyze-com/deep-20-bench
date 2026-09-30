import type { RouteLocationNormalizedLoaded, Router } from "vue-router";

import { createVisitorIdReader } from "./visitor-id";

interface Pageview {
  readonly url: string;
  readonly title: string;
  readonly referrer: string;
  readonly id?: string;
}

declare global {
  interface Window {
    umami?: {
      track: (payload: (defaults: Pageview) => Pageview) => void | Promise<void>;
      identify?: (id: string) => void | Promise<void>;
    };
  }
}

declare module "vue-router" {
  interface RouteMeta {
    /** Routes are tracked by default; opt out only for non-content pages. */
    trackPageview?: boolean;
  }
}

/** Install after initial routing settles. Analytics never blocks the application. */
export const installPageviewTracking = (router: Router): (() => void) => {
  const script = document.getElementById("deep20-analytics");
  if (!(script instanceof HTMLScriptElement)) return () => undefined;

  let pending: Pageview[] = [];
  let previousPath: string | null = null;
  let previousUrl = document.referrer;
  let disabled = false;
  const getVisitorId = createVisitorIdReader();
  let identifiedVisitorId: string | undefined;

  const flush = (): void => {
    const tracker = window.umami;
    if (disabled || !pending.length || typeof tracker?.track !== "function") return;
    const pageviews = pending;
    pending = [];
    for (const pageview of pageviews) {
      const visitorId = getVisitorId();
      if (visitorId !== identifiedVisitorId) {
        identifiedVisitorId = visitorId;
        try {
          // Umami sets its distinct ID synchronously before its identify request.
          void Promise.resolve(tracker.identify?.(visitorId)).catch(() => undefined);
        } catch {
          // Keep recording views if identification is unsupported or fails.
        }
      }
      try {
        // Snapshot each visit, including its title and referrer, before a late tracker
        // loads. Using the tracker's current URL would misattribute earlier visits.
        void Promise.resolve(tracker.track(defaults => ({ ...defaults, ...pageview, id: visitorId })))
          .catch(() => undefined);
      } catch {
        // Optional analytics must not break rendering or later navigation.
      }
    }
  };
  const disable = (): void => {
    disabled = true;
    pending = [];
  };
  const record = (route: RouteLocationNormalizedLoaded): void => {
    if (disabled) return;
    const url = new URL(router.resolve(route.fullPath).href, window.location.href);
    url.hash = "";
    const path = url.pathname.replace(/\/+$/, "") || "/";
    // Query parameters, anchors, and a trailing slash do not identify another page.
    if (path === previousPath) return;
    const referrer = previousUrl;
    previousPath = path;
    previousUrl = url.href;
    if (route.meta.trackPageview === false) return;
    pending.push({ url: url.href, title: document.title, referrer });
    flush();
  };

  script.addEventListener("load", flush);
  script.addEventListener("error", disable);
  const removeAfterEach = router.afterEach((to, _from, failure) => {
    if (!failure) record(to);
  });
  record(router.currentRoute.value);
  return () => {
    disable();
    removeAfterEach();
    script.removeEventListener("load", flush);
    script.removeEventListener("error", disable);
  };
};
