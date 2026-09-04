import type { RouteMetadata } from "./route-metadata";

/** Keep the browser head aligned with the same metadata used for initial HTML. */
export const applyPageMetadata = (
  metadata: RouteMetadata | undefined,
  canonicalBase: string,
): void => {
  if (typeof document === "undefined") return;

  const title = metadata?.browser_title ?? "Page not found · Deep20Bench";
  const description = metadata?.description ??
    "The requested Deep20Bench page is not in the current publication.";
  const canonicalUrl = metadata === undefined ? null : new URL(
    metadata.canonical_route === "" ? "" : `${metadata.canonical_route}/`,
    canonicalBase,
  ).href;

  const setMeta = (attribute: "name" | "property", name: string, content: string): void => {
    let element = document.querySelector<HTMLMetaElement>(`meta[${attribute}="${name}"]`);
    if (element === null) {
      element = document.createElement("meta");
      element.setAttribute(attribute, name);
      document.head.append(element);
    }
    element.content = content;
  };

  document.title = title;
  setMeta("name", "description", description);
  setMeta("property", "og:title", title);
  setMeta("property", "og:description", description);
  setMeta("name", "twitter:title", title);
  setMeta("name", "twitter:description", description);

  let canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (canonicalUrl === null) {
    canonical?.remove();
    document.querySelector('meta[property="og:url"]')?.remove();
  } else {
    if (canonical === null) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.append(canonical);
    }
    canonical.href = canonicalUrl;
    setMeta("property", "og:url", canonicalUrl);
  }

  if (metadata?.indexable === true) {
    document.querySelector('meta[name="robots"]')?.remove();
  } else {
    setMeta("name", "robots", "noindex, follow");
  }
};
