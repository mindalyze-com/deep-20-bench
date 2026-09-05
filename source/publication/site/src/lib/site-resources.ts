export interface SiteResourceLink {
  readonly href: string;
  readonly label: string;
}

const repository = "https://github.com/mindalyze-com/deep-20-bench";

export const citationResource: SiteResourceLink = {
  href: `${repository}/blob/main/CITATION.cff`,
  label: "Citation metadata",
};

export const dataLicenseResource: SiteResourceLink = {
  href: "https://creativecommons.org/licenses/by/4.0/",
  label: "CC BY 4.0 data licence",
};

export const softwareLicenseDescription =
  "The software is source-available under a dual-license model: PolyForm Noncommercial " +
  "for noncommercial use, with separate commercial licenses available.";

export const softwareLicenseResource: SiteResourceLink = {
  href: `${repository}/blob/main/LICENSE.md`,
  label: "Software licensing - source-available",
};

export const supportResource: SiteResourceLink = {
  href: "https://ko-fi.com/mindalyze",
  label: "Support on Ko-fi",
};

export const citeAndReuseLinks: readonly SiteResourceLink[] = [
  { ...citationResource, label: "How to cite" },
  { ...dataLicenseResource, label: "Result data licence - CC BY 4.0" },
  softwareLicenseResource,
];

export const contributionLinks: readonly SiteResourceLink[] = [
  { href: `${repository}/discussions`, label: "Suggest a model or contact us" },
  supportResource,
  { href: `${repository}/issues/new/choose`, label: "Report an error" },
  { href: repository, label: "Source repository" },
];

export const siteResourceLinks: readonly SiteResourceLink[] = [
  ...citeAndReuseLinks,
  ...contributionLinks,
];
