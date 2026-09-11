import {
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const requiredEnvironment = (name) => {
  const value = process.env[name];
  if (value === undefined || value.length === 0) {
    throw new Error(`${name} is required for publication prerendering.`);
  }
  return value;
};

const outputRoot = resolve(requiredEnvironment("DEEP20_OUTPUT_DIR"));
const publicRoot = resolve(requiredEnvironment("DEEP20_PUBLIC_DIR"));
const serverRoot = resolve(requiredEnvironment("DEEP20_SSR_OUTPUT_DIR"));
const routeManifestPath = resolve(requiredEnvironment("DEEP20_ROUTE_MANIFEST"));
const configuredCanonicalUrl = requiredEnvironment("DEEP20_CANONICAL_URL");
const canonicalUrl = configuredCanonicalUrl.endsWith("/")
  ? configuredCanonicalUrl
  : `${configuredCanonicalUrl}/`;

const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));
const objectValue = (value, label) => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value;
};
const stringValue = (value, label) => {
  if (typeof value !== "string") throw new Error(`${label} must be a string.`);
  return value;
};
const booleanValue = (value, label) => {
  if (typeof value !== "boolean") throw new Error(`${label} must be a boolean.`);
  return value;
};
const nullableStringValue = (value, label) => {
  if (value !== null && typeof value !== "string") {
    throw new Error(`${label} must be a string or null.`);
  }
  return value;
};

const parseRouteManifest = (value) => {
  const manifest = objectValue(value, "route manifest");
  if (manifest.schema_version !== 2 || !Array.isArray(manifest.routes)) {
    throw new Error("Static route manifest schema version 2 is required.");
  }
  const supportedKinds = new Set([
    "home",
    "editorial",
    "run",
    "alias",
    "subject",
    "episode",
  ]);
  return manifest.routes.map((candidate, index) => {
    const route = objectValue(candidate, `routes[${index}]`);
    const kind = stringValue(route.kind, `routes[${index}].kind`);
    if (!supportedKinds.has(kind)) throw new Error(`Unsupported route kind ${kind}.`);
    return {
      route: stringValue(route.route, `routes[${index}].route`),
      editionId: stringValue(route.edition_id, `routes[${index}].edition_id`),
      kind,
      indexable: booleanValue(route.indexable, `routes[${index}].indexable`),
      sitemapIncluded: booleanValue(
        route.sitemap_included,
        `routes[${index}].sitemap_included`,
      ),
      canonicalRoute: stringValue(
        route.canonical_route,
        `routes[${index}].canonical_route`,
      ),
      browserTitle: stringValue(
        route.browser_title,
        `routes[${index}].browser_title`,
      ),
      description: stringValue(route.description, `routes[${index}].description`),
      lastModified: stringValue(
        route.last_modified,
        `routes[${index}].last_modified`,
      ),
      executionId: nullableStringValue(
        route.execution_id,
        `routes[${index}].execution_id`,
      ),
      targetId: nullableStringValue(
        route.target_id,
        `routes[${index}].target_id`,
      ),
      trialId: nullableStringValue(
        route.trial_id,
        `routes[${index}].trial_id`,
      ),
    };
  });
};

const routes = parseRouteManifest(readJson(routeManifestPath));
const clientTemplateSource = readFileSync(join(outputRoot, "index.html"), "utf8");
const ssrManifest = objectValue(
  readJson(join(outputRoot, ".vite", "ssr-manifest.json")),
  "SSR asset manifest",
);
const editionsDocument = readJson(join(publicRoot, "data", "editions.json"));
const editionManifests = new Map(editionsDocument.editions.map(edition => [edition.edition_id,
  readJson(join(publicRoot, "data", edition.manifest_path))]));
const editionLeaderboards = new Map(editionsDocument.editions.map(edition => [edition.edition_id,
  readJson(join(publicRoot, "data", edition.leaderboard_path))]));
const manifestDocument = editionManifests.get(editionsDocument.default_edition_id);
const runDocuments = new Map(editionsDocument.editions.flatMap(edition => edition.runs).map(reference => {
  const document = readJson(join(publicRoot, "data", "runs", `${reference.execution_id}.json`));
  return [reference.execution_id, document];
}));
const subjectDocuments = new Map(
  routes
    .filter((route) => route.kind === "subject")
    .map((route) => {
      if (route.executionId === null || route.targetId === null) {
        throw new Error(`Missing subject identity for ${route.route}.`);
      }
      const document = readJson(
        join(
          publicRoot,
          "data",
          "runs",
          route.executionId,
          "subjects",
          `${route.targetId}.json`,
        ),
      );
      return [`${route.executionId}/${route.targetId}`, document];
    }),
);

const serverEntryPath = join(serverRoot, "entry-server.js");
const { renderPublicationPage, homepageStructuredData } = await import(pathToFileURL(serverEntryPath).href);

const escapeHtml = (value) =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
const escapeXml = (value) =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
const safeJson = (value) =>
  JSON.stringify(value)
    .replaceAll("<", "\\u003c")
    .replaceAll(">", "\\u003e")
    .replaceAll("&", "\\u0026")
    .replaceAll("\u2028", "\\u2028")
    .replaceAll("\u2029", "\\u2029");

const replaceUnique = (html, pattern, replacement, label) => {
  const matches = html.match(pattern);
  if (matches === null || matches.length !== 1) {
    throw new Error(`Expected exactly one ${label} in the client template.`);
  }
  return html.replace(pattern, replacement);
};

const clientTemplate = replaceUnique(
  clientTemplateSource,
  /<meta property="og:site_name" content="[^"]*" \/>/g,
  `<meta property="og:site_name" content="${escapeHtml(manifestDocument.site.title)}" />`,
  "Open Graph site name",
);

// Async route styles must be present before the first paint of their static HTML.
// Vite's manifest already includes the configured base and content-hashed filenames.
const withPageStyles = (modules) => {
  const included = new Set(
    [...clientTemplate.matchAll(/<link\b[^>]*\brel="stylesheet"[^>]*\bhref="([^"]+)"/g)]
      .map((match) => match[1]),
  );
  const links = [];
  for (const module of modules) {
    const assets = ssrManifest[module] ?? [];
    if (!Array.isArray(assets)) throw new Error(`Invalid SSR assets for ${module}.`);
    for (const value of assets) {
      const asset = stringValue(value, "SSR asset");
      if (!asset.endsWith(".css") || included.has(asset)) continue;
      included.add(asset);
      links.push(`    <link rel="stylesheet" crossorigin href="${escapeHtml(asset)}">`);
    }
  }
  return links.length === 0
    ? clientTemplate
    : clientTemplate.replace("  </head>", `${links.join("\n")}\n  </head>`);
};

const routeUrl = (route) =>
  route.length === 0 ? canonicalUrl : `${canonicalUrl}${route}/`;

const pageDocuments = (route) => {
  const manifest = editionManifests.get(route.editionId);
  const leaderboard = editionLeaderboards.get(route.editionId);
  if (manifest === undefined || leaderboard === undefined) throw new Error(`Missing edition ${route.editionId}`);
  const localRoute = route.route.replace(/^editions\/[^/]+(?:\/|$)/, "");
  const documents = [editionsDocument, manifest];
  const needsLeaderboard = route.kind === "home" || route.kind === "run" ||
    localRoute === "results" || localRoute.startsWith("results/");
  if (needsLeaderboard) documents.push(leaderboard);
  if (localRoute === "methodology") {
    documents.push(...[...editionManifests.values()].filter(item => item.edition_id !== route.editionId));
  }
  if (localRoute === "results/cost" || localRoute === "results/time") {
    documents.push(...manifest.official_runs.map(reference => runDocuments.get(reference.execution_id)));
  } else if (route.kind === "run") {
    const run = runDocuments.get(route.executionId);
    if (run === undefined) throw new Error(`Missing run data for ${route.route}.`);
    documents.push(run);
  } else if (route.kind === "subject") {
    const run = runDocuments.get(route.executionId);
    const subject = subjectDocuments.get(`${route.executionId}/${route.targetId}`);
    if (run === undefined || subject === undefined) throw new Error(`Missing subject data for ${route.route}.`);
    documents.push(run, subject);
  }
  return documents;
};

const renderable = (route) =>
  ["home", "editorial", "run", "alias", "subject"].includes(route.kind);

const metadataHtml = (template, route, appHtml, documents) => {
  const canonical = routeUrl(route.canonicalRoute);
  const image = new URL("og.webp", canonicalUrl).href;
  let html = template;
  html = replaceUnique(
    html,
    /<meta\s+name="description"\s+content="[^"]*"\s*\/>/g,
    `<meta name="description" content="${escapeHtml(route.description)}" />`,
    "description",
  );
  html = replaceUnique(
    html,
    /<meta property="og:title" content="[^"]*" \/>/g,
    `<meta property="og:title" content="${escapeHtml(route.browserTitle)}" />`,
    "Open Graph title",
  );
  html = replaceUnique(
    html,
    /<meta\s+property="og:description"\s+content="[^"]*"\s*\/>/g,
    `<meta property="og:description" content="${escapeHtml(route.description)}" />`,
    "Open Graph description",
  );
  html = replaceUnique(
    html,
    /<meta property="og:url" content="[^"]*" \/>/g,
    `<meta property="og:url" content="${escapeHtml(canonical)}" />`,
    "Open Graph URL",
  );
  html = replaceUnique(
    html,
    /<meta property="og:image" content="[^"]*" \/>/g,
    `<meta property="og:image" content="${escapeHtml(image)}" />`,
    "Open Graph image",
  );
  html = replaceUnique(
    html,
    /<meta name="twitter:title" content="[^"]*" \/>/g,
    `<meta name="twitter:title" content="${escapeHtml(route.browserTitle)}" />`,
    "Twitter title",
  );
  html = replaceUnique(
    html,
    /<meta\s+name="twitter:description"\s+content="[^"]*"\s*\/>/g,
    `<meta name="twitter:description" content="${escapeHtml(route.description)}" />`,
    "Twitter description",
  );
  html = replaceUnique(
    html,
    /<link rel="canonical" href="[^"]*" \/>/g,
    `<link rel="canonical" href="${escapeHtml(canonical)}" />`,
    "canonical URL",
  );
  html = replaceUnique(
    html,
    /<title>.*?<\/title>/gs,
    `<title>${escapeHtml(route.browserTitle)}</title>`,
    "document title",
  );
  html = replaceUnique(
    html,
    /<!-- deep20-structured-data -->/g,
    route.kind === "home"
      ? homepageStructuredData(
          editionManifests.get(route.editionId),
          editionLeaderboards.get(route.editionId),
          canonicalUrl,
        ).map((data) => `<script type="application/ld+json">${safeJson(data)}</script>`).join("\n    ")
      : "",
    "structured-data marker",
  );
  if (!route.indexable) {
    html = html.replace(
      "</head>",
      '    <meta name="robots" content="noindex, follow" />\n  </head>',
    );
  }
  if (renderable(route)) {
    html = replaceUnique(
      html,
      /<html lang="en">/g,
      '<html lang="en" data-prerendered="true">',
      "HTML root",
    );
    html = replaceUnique(
      html,
      /<div id="app"><\/div>/g,
      `<div id="app">${appHtml}</div>`,
      "application root",
    );
    const state = safeJson({ schema_version: 1, documents });
    html = html.replace(
      "</body>",
      `<script id="deep20-page-state" type="application/json">${state}</script>\n  </body>`,
    );
  }
  return html.replace(/[ \t]+$/gm, "");
};

for (const route of routes) {
  const documents = pageDocuments(route);
  const rendered = renderable(route)
    ? await renderPublicationPage(
        route.route.length === 0 ? "/" : `/${route.route}/`,
        documents,
      )
    : { appHtml: "", modules: [] };
  const html = metadataHtml(withPageStyles(rendered.modules), route, rendered.appHtml, documents);
  const output =
    route.route.length === 0
      ? join(outputRoot, "index.html")
      : join(outputRoot, route.route, "index.html");
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, html, "utf8");
}

let notFound = clientTemplate;
notFound = notFound.replace(
  "</head>",
  '    <meta name="robots" content="noindex, follow" />\n  </head>',
);
notFound = replaceUnique(
  notFound,
  /<link rel="canonical" href="[^"]*" \/>/g,
  "",
  "404 canonical URL",
);
notFound = replaceUnique(
  notFound,
  /<!-- deep20-structured-data -->/g,
  "",
  "404 structured-data marker",
);
writeFileSync(join(outputRoot, "404.html"), notFound.replace(/[ \t]+$/gm, ""), "utf8");

const sitemapLocations = routes
  .filter((route) => route.sitemapIncluded)
  .map(
    (route) =>
      `  <url>\n    <loc>${escapeXml(routeUrl(route.canonicalRoute))}</loc>\n    <lastmod>${escapeXml(route.lastModified)}</lastmod>\n  </url>`,
  )
  .join("\n");
writeFileSync(
  join(outputRoot, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${sitemapLocations}\n</urlset>\n`,
  "utf8",
);

const canonicalAddress = new URL(canonicalUrl);
if (canonicalAddress.pathname === "/") {
  writeFileSync(
    join(outputRoot, "robots.txt"),
    `User-agent: *\nAllow: /\n\nSitemap: ${new URL("sitemap.xml", canonicalUrl).href}\n`,
    "utf8",
  );
  if (
    canonicalAddress.hostname !== "github.io" &&
    !canonicalAddress.hostname.endsWith(".github.io")
  ) {
    writeFileSync(join(outputRoot, "CNAME"), `${canonicalAddress.hostname}\n`, "utf8");
  }
}
rmSync(join(outputRoot, ".vite"), { recursive: true, force: true });
rmSync(serverRoot, { recursive: true, force: true });
