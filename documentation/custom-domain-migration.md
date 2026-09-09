# Deep20Bench custom domain

The publication is hosted at `https://deep20bench.com/`. Its base path is `/`.
`config/publication.yml` supplies the canonical URL, and the frontend defaults match it.
The prerenderer derives CNAME and robots.txt from that URL for a domain-root build, keeping
them in `docs/` through every regeneration. Keep them with every publication.

## Verified state - 7 September 2026

Read-only DNS, HTTPS, and GitHub Pages API checks confirmed:

- The apex has all four GitHub Pages A and AAAA records; `www` points to
  `mindalyze-com.github.io`.
- GitHub Pages uses `main:/docs`, reports a built site, and has `deep20bench.com` as its CNAME.
- The certificate is approved for the apex and `www`, and HTTPS enforcement is enabled.
- The HTTPS homepage, robots.txt, and sitemap.xml return 200. `www` redirects to the apex.
- The original GitHub Pages v9 dataset and schema addresses redirect to the same paths on
  `deep20bench.com`, both returning 200 with JSON content type.

The saved zone at `config/dns/deep20bench.com.zone` retains the GitHub verification TXT record
observed during the original 4 September setup. Search Console ownership/submission was not
checked. Local generation and external deployment are separate: these hosting checks do not
mean that uncommitted local output is already deployed.

## Deployment

Follow the repository's explicit authorization rule before committing, pushing, or changing
external hosting settings. Publication uses `main:/docs`; never push the development branch.
For a later authorized deployment, publish the complete regenerated output and recheck the
existing custom-domain and HTTPS settings. Configure only this project; the account also
hosts MTL Explorer. Follow the
[GitHub custom-domain procedure](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

After deployment, check HTTPS on the apex, the `www` redirect, and direct editorial, result,
run, subject, and episode URLs. Check assets and JSON requests, initial and hydrated metadata,
canonical URLs, homepage WebSite and Dataset JSON-LD, robots.txt, and sitemap.xml.

The original compatibility address is
`https://mindalyze-com.github.io/deep-20-bench/data/deep20bench-v9.json`.
Keep its v9 schema available as well. The current build retains both files with current data;
the v9 site metadata uses base path `/`, and its schema accepts root and project paths.
Recheck the old dataset and schema redirects after each deployment and validate the downloaded
JSON against its companion schema.
Verify old run and subject URLs also reach their corresponding pages on the new domain.

Verify the new Search Console property and submit `https://deep20bench.com/sitemap.xml`.
Request a homepage recrawl after the new metadata is live. Do not submit a host-wide Change of
Address for `mindalyze-com.github.io`: it also hosts other projects, and the tool does not accept
the old project path as a source property. See
[Search Console's scope rules](https://support.google.com/webmasters/answer/9370220).

The domain's site name and title remain Google's automated choices; correct root metadata
makes the preferred identity eligible but does not guarantee wording or ranking.
