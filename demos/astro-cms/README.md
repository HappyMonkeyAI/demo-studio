# Demo pack: astro-cms

Throwaway / lawyer-demo site only. **Never** point `DEMO_BASE_URL` at a confidential pilot or `client-data/`.

```bash
export DEMO_BASE_URL=http://127.0.0.1:NNNN   # your throwaway site
demo-studio validate demos/astro-cms/demo.beats.json
demo-studio dry-run demos/astro-cms/demo.beats.json
# Phase 1+: demo-studio dry-run … --execute-neo
```

Beats: public home → SSO login chooser → password sign-in → Home page editor → plugins manager → WordPress import wizard → migration issues → agent approvals → outro.

WordPress import in admin is EmDash’s Connect / Review / Import wizard (key, URL, or WXR upload). The deeper go-live / forms / redirects passes used on this throwaway were driven via `wp-migrate` CLI.
