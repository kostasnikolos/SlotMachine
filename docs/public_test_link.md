# Putting the game on a public link for testers

The game stays on your PC (or any box with Docker); a Cloudflare Tunnel gives it an https address. No router ports are
opened, no server is rented, and the container is read-only with the debug endpoints off (`docker-compose.yml`).

## 1. One-off: install Docker Desktop

https://www.docker.com/products/docker-desktop/ (Windows, WSL2 backend). Reboot if it asks.

## 2. Quick link (no account, changes on every restart)

```bash
docker compose --profile tunnel up -d --build
```
```bash
docker compose logs tunnel | grep -o "https://[a-z0-9-]*\.trycloudflare\.com"
```

Send the printed `https://…trycloudflare.com` address. It opens the canvas front end directly (`/` redirects to it).
The address dies when the tunnel container stops; the next start prints a new one.

## 3. Stable link (your own hostname, free Cloudflare account)

1. Cloudflare Zero Trust → Networks → Tunnels → Create a tunnel (Cloudflared) → copy the token.
2. Put it in a `.env` file next to `docker-compose.yml` (git-ignored):
   ```
   TUNNEL_TOKEN=eyJ...
   ```
3. In the tunnel's Public Hostname tab, map `descent.yourdomain.com` → `http://slot:8080`.
4. `docker compose --profile tunnel up -d --build`. The hostname stays the same across restarts.
5. Optional, recommended for a private test: Zero Trust → Access → Applications → add the hostname with a policy
   "Emails ending in @yourcompany.gr" or a one-time-PIN list. Testers log in once; nobody else can open the page.

## 4. What testers get and what protects you

- The page shows "DEMO BUILD · PLAY MONEY ONLY · NO REAL WAGERING · 18+" at the bottom.
- Paid endpoints are rate-limited per client (4 spins/s sustained, burst 20; `SLOT_RATE_PER_SEC` / `SLOT_RATE_BURST`).
- Balance lives in the browser: nothing a tester does changes anything on your side; a refresh resets them to 1,000.
- The container cannot write to disk; `/api/snapshot` and `/api/upload-model` answer 404.
- `docker compose logs slot` shows every spin the engine served.

## 5. Updating the running demo

```bash
git pull && docker compose --profile tunnel up -d --build
```

## 6. Stop

```bash
docker compose --profile tunnel down
```
