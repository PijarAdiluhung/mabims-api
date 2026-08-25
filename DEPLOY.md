# Deployment Runbook

Everything code-side is committed; this is the click-path to go live. Two domains assumed:
`api.mabims.dev` → API container, `mabims.dev` → docs container (rename everywhere).

## 1. Environment

| Variable | Where | Example |
|---|---|---|
| `ALLOWED_ORIGINS` | api service | `*` (default, public) or comma-separated origins to restrict |
| `RATE_LIMIT` | api service | `240/minute` |
| `MABIMS_FALLBACK_DIR` | api service | already `/data` in compose — leave it |
| `PUBLIC_API_BASE` | **build arg** for docs | `https://api.mabims.dev` |

Reads are public by default (`ALLOWED_ORIGINS=*`). If you ever need to restrict browser
access, set exact origins there; apex/subdomain rules use `ALLOWED_ORIGIN_SUFFIXES`.

## 2. Dokploy

1. New Project → **Compose** service → point at this repo.
2. Paste env vars above into the service's environment tab (`PUBLIC_API_BASE` goes under
   build args).
3. Deploy once so both images build.
4. **Domains** tab:
   - `api.mabims.dev` → service `api`, port `8000`
   - `mabims.dev` → service `docs`, port `80`
5. Traefik issues certificates automatically; verify HTTPS on both.

## 3. Bunny CDN

One pull zone per domain (or one zone with two origins — your call):

1. Create pull zone `mabims-api`, origin `api.mabims.dev` (origin URL with `https://`).
2. **Caching** tab:
   - Cache Expiration: enable **"Respect origin headers / Override Cache Time = off"**
     (Bunny must honour our dynamic `s-maxage`)
   - Query string: include all parameters (default)
3. Repeat for `mabims-docs` zone → origin `mabims.dev`; here you *can* override cache time
   aggressively since assets are hashed.
4. Point DNS CNAMEs at Bunny endpoints; enable SSL for the bunny hostname.

## 4. Smoke checklist

```bash
curl -s https://api.mabims.dev/healthz
curl -sI https://api.mabims.dev/api/v1/today          # expect s-maxage=<seconds to midnight>
curl -s "https://api.mabims.dev/api/v1/convert?date=2025-01-03&calendar=gregorian"
curl -si -H "Origin: https://any.site" https://api.mabims.dev/api/v1/today | head -1   # 200, CORS echoed
```

**Cache verification**: hit `/today` twice from a browser devtools "disable cache OFF"
window; watch Dokploy api logs — second hit should produce no access log entry (served by
Bunny). Then confirm Bunny zone stats tick up.

## 5. Cutover

- [ ] Repoint partner integrations to `https://api.mabims.dev/api/v1/*`
- [ ] Partners verify in production for a week (old Netlify stays live meanwhile)
- [ ] Disable Netlify function + old domain redirect
- [ ] Update README/docs URLs if final hostnames differ from placeholders
