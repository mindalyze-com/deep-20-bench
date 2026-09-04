/** Public page metadata projected from the compiler's StaticRouteManifest. */
export interface RouteMetadata {
  readonly route: string;
  readonly canonical_route: string;
  readonly browser_title: string;
  readonly description: string;
  readonly indexable: boolean;
}

export const parseRouteMetadata = (value: unknown): readonly RouteMetadata[] => {
  if (
    typeof value !== "object" || value === null ||
    !("schema_version" in value) || value.schema_version !== 2 ||
    !("routes" in value) || !Array.isArray(value.routes)
  ) {
    throw new Error("Static route manifest schema version 2 is required.");
  }
  const paths = new Set<string>();
  return value.routes.map((route: unknown): RouteMetadata => {
    if (
      typeof route !== "object" || route === null ||
      !("route" in route) || typeof route.route !== "string" ||
      !("canonical_route" in route) || typeof route.canonical_route !== "string" ||
      !("browser_title" in route) || typeof route.browser_title !== "string" ||
      route.browser_title.trim().length === 0 ||
      !("description" in route) || typeof route.description !== "string" ||
      route.description.trim().length === 0 ||
      !("indexable" in route) || typeof route.indexable !== "boolean"
    ) {
      throw new Error("Static route metadata is invalid.");
    }
    if (paths.has(route.route)) throw new Error("Static route metadata has duplicate paths.");
    paths.add(route.route);
    return {
      route: route.route,
      canonical_route: route.canonical_route,
      browser_title: route.browser_title,
      description: route.description,
      indexable: route.indexable,
    };
  });
};
