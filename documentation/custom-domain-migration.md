# Deep20Bench custom domain

The publication is prepared for `https://deep20bench.com/`. Its base path is `/`.
`config/publication.yml` supplies the canonical URL, and the frontend defaults match it.
The prerenderer derives CNAME and robots.txt from that URL for a domain-root build, keeping
them in `docs/` through every regeneration. Keep them with every publication.

DNS was checked on 4 September 2026: the apex has all four GitHub Pages A and AAAA records;
`www` points to `mindalyze-com.github.io`; the GitHub verification TXT record is visible.
The saved zone at `config/dns/deep20bench.com.zone` retains that verification record.
At this check, the repository's Pages custom-domain field was still unset.

## Deployment

Follow the repository's explicit authorization rule before committing, pushing, or changing
external hosting settings. Publication uses `main:/docs`; never push the development branch.
Assign `deep20bench.com` to this project's Pages settings, deploy the complete reviewed output,
and confirm that GitHub issues the certificate and HTTPS enforcement is active. Configure only
this project; the account also hosts MTL Explorer. Follow the
[GitHub custom-domain procedure](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

After deployment, check HTTPS on the apex, the `www` redirect, and direct editorial, result,
run, subject, and episode URLs. Check assets and JSON requests, initial and hydrated metadata,
canonical URLs, homepage WebSite and Dataset JSON-LD, robots.txt, and sitemap.xml.

The original compatibility address is
`https://mindalyze-com.github.io/deep-20-bench/data/deep20bench-v9.json`.
Keep its v9 schema available as well. The current build retains both files with current data;
the v9 site metadata changes to base path `/`, and its schema accepts root and project paths.
Verify that the old address follows any hosting redirect to current valid JSON and that the
old schema address remains usable. Do not assume this succeeds until tested against GitHub.
Verify old run and subject URLs also reach their corresponding pages on the new domain.

Verify the new Search Console property and submit `https://deep20bench.com/sitemap.xml`.
Request a homepage recrawl after the new metadata is live. Do not submit a host-wide Change of
Address for `mindalyze-com.github.io`: it also hosts other projects, and the tool does not accept
the old project path as a source property. See
[Search Console's scope rules](https://support.google.com/webmasters/answer/9370220).

The domain's site name and title remain Google's automated choices; correct root metadata
makes the preferred identity eligible but does not guarantee wording or ranking.
