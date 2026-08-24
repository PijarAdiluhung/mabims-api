# Deployment Runbook

Everything code-side is committed; this is the click-path to go live. Two domains assumed:
`api.example.com` → API container, `example.com` → docs container (rename everywhere).

## 1. Environment

| Variable | Where | Example |
|---|---|---|
| `ALLOWED_ORIGINS` | api service | `https://malangmengaji.com,https://peta-malangmengaji.web.app` |
| `RATE_LIMIT` | api service | `240/minute` |
| `MABIMS_FALLBACK_DIR` | api service | already `/data` in compose — leave it |
| `PUBLIC_API_BASE` | **build arg** for docs | `https://api.example.com` |

Apex/subdomains of `malangmengaji.com` are always allowed via suffix rule; add other exact
origins through `ALLOWED_ORIGINS`.

## 2. Dokploy

1. New Project → **Compose** service → point at this repo.
2. Paste env vars above into the service's environment tab (`PUBLIC_API_BASE` goes under
   build args).
3. Deploy once so both images build.
4. **Domains** tab:
   - `api.example.com` → service `api`, port `8000`
   - `example.com` → service `docs`, port `80`
5. Traefik issues certificates automatically; verify HTTPS on both.

## 3. Bunny CDN

One pull zone per domain (or one zone with two origins — your call):

1. Create pull zone `mabims-api`, origin `api.example.com` (origin URL with `https://`).
2. **Caching** tab:
   - Cache Expiration: enable **"Respect origin headers / Override Cache Time = off"**
     (Bunny must honour our dynamic `s-maxage`)
   - Query string: include all parameters (default)
3. Repeat for `mabims-docs` zone → origin `example.com`; here you *can* override cache time
   aggressively since assets are hashed.
4. Point DNS CNAMEs at Bunny endpoints; enable SSL for the bunny hostname.

## 4. Smoke checklist

```bash
curl -s https://api.example.com/healthz
curl -sI https://api.example.com/api/v1/today          # expect s-maxage=<seconds to midnight>
curl -s "https://api.example.com/api/v1/convert?date=2025-01-03&calendar=gregorian"
curl -si -H "Origin: https://evil.example" https://api.example.com/api/v1/today | head -1   # 403
curl -si -H "Origin: https://malangmengaji.com" https://api.example.com/api/v1/today | head -1  # 200
```

**Cache verification**: hit `/today` twice from a browser devtools "disable cache OFF"
window; watch Dokploy api logs — second hit should produce no access log entry (served by
Bunny). Then confirm Bunny zone stats tick up.

## 5. Cutover

- [ ] Repoint partner integrations to `https://api.example.com/api/v1/*`
- [ ] Partners verify in production for a week (old Netlify stays live meanwhile)
- [ ] Disable Netlify function + old domain redirect
- [ ] Update README/docs URLs if final hostnames differ from placeholders
