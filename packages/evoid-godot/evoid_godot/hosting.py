"""Game Hosting — serve Godot WebGL exports with instant loading.

Manages multiple game builds. Each build is a Godot HTML5 export directory.
The host serves the game with:
- Instant splash screen (inline HTML/CSS, no external deps)
- Streaming engine.wasm with progress tracking
- Chunked game.pck loading (256KB chunks)
- Service Worker for caching (instant repeat visits)
- Multi-game support at /game/{game_id}/

This module is purely additive — it does not modify any existing EVOID code.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.applications import Starlette
    from starlette.routing import Mount


@dataclass
class SplashConfig:
    """Splash screen customization."""

    bg_color: str = "#1a1a2e"
    text_color: str = "#ffffff"
    accent_color: str = "#e94560"
    logo_url: str | None = None
    title: str = ""
    subtitle: str = "Powered by EVOID"


@dataclass
class GameBuild:
    """A registered Godot WebGL export build."""

    game_id: str
    build_dir: Path
    title: str
    splash: SplashConfig
    manifest: dict = field(default_factory=dict)
    chunk_size: int = 256 * 1024  # 256KB

    def scan(self) -> None:
        """Scan build directory and populate manifest."""
        self.manifest = {"game_id": self.game_id, "files": {}}
        if not self.build_dir.exists():
            return
        for f in sorted(self.build_dir.rglob("*")):
            if f.is_file():
                rel = str(f.relative_to(self.build_dir))
                self.manifest["files"][rel] = {
                    "size": f.stat().st_size,
                    "hash": hashlib.md5(f.read_bytes()[:4096]).hexdigest()[:8],
                }
        self.manifest["total_size"] = sum(
            v["size"] for v in self.manifest["files"].values()
        )
        self.manifest["pck_chunks"] = self._count_pck_chunks()

    def _count_pck_chunks(self) -> int:
        pck = self.build_dir / "game.pck"
        if not pck.exists():
            return 0
        return -(-pck.stat().st_size // self.chunk_size)  # ceil division


class GameHost:
    """Manages multiple game builds. Zero side effects on existing EVOID code."""

    def __init__(self, chunk_size: int = 256 * 1024) -> None:
        self.builds: dict[str, GameBuild] = {}
        self.chunk_size = chunk_size

    def register_build(
        self,
        game_id: str,
        build_dir: str | Path,
        title: str = "",
        splash: SplashConfig | None = None,
    ) -> None:
        """Register a Godot WebGL export build."""
        path = Path(build_dir)
        if not path.exists():
            raise FileNotFoundError(f"Build directory not found: {path}")

        build = GameBuild(
            game_id=game_id,
            build_dir=path,
            title=title or game_id,
            splash=splash or SplashConfig(title=title or game_id),
            chunk_size=self.chunk_size,
        )
        build.scan()
        self.builds[game_id] = build

    def get_build(self, game_id: str) -> GameBuild | None:
        return self.builds.get(game_id)

    def create_app(self, game_id: str) -> Starlette:
        """Create a per-game ASGI app with all routes."""
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.staticfiles import StaticFiles

        build = self.builds.get(game_id)
        if not build:
            raise ValueError(f"Game '{game_id}' not registered")

        routes = [
            Route("/", self._make_index_handler(build)),
            Route("/manifest.json", self._make_manifest_handler(build)),
            Route("/sw.js", self._make_sw_handler(build)),
            Route("/engine.wasm", self._make_wasm_handler(build)),
            Route("/game.pck", self._make_pck_handler(build)),
            Route("/chunk/{chunk_n:int}", self._make_chunk_handler(build)),
            Mount("/assets", app=StaticFiles(directory=str(build.build_dir)), name="assets"),
        ]
        return Starlette(routes=routes)

    def create_router(self) -> Mount:
        """Create a multi-game router: /game/{game_id}/..."""
        from starlette.routing import Mount, Route

        async def game_entry(request):
            """Redirect /game/ to list of games."""
            from starlette.responses import JSONResponse

            games = []
            for gid, build in self.builds.items():
                games.append({
                    "game_id": gid,
                    "title": build.title,
                    "url": f"/game/{gid}/",
                    "total_size": build.manifest.get("total_size", 0),
                })
            return JSONResponse({"games": games})

        # Create a sub-router that maps game_id to its app
        app_map = {}
        for gid, build in self.builds.items():
            app_map[gid] = self.create_app(gid)

        async def game_dispatch(scope, receive, send):
            """Route /game/{game_id}/... to the correct game app."""
            from starlette.responses import JSONResponse

            path = scope.get("path", "")
            parts = path.strip("/").split("/")
            # Expected: ["game", "{game_id}", ...]
            if len(parts) < 2 or parts[0] != "game":
                return await game_entry(scope, receive, send)

            game_id = parts[1]
            if game_id not in app_map:
                return await JSONResponse(
                    {"error": f"Game '{game_id}' not found"}, status_code=404
                )(scope, receive, send)

            # Rewrite path for the sub-app
            sub_scope = dict(scope)
            sub_scope["path"] = "/" + "/".join(parts[2:])
            sub_scope["raw_path"] = sub_scope["path"].encode()
            return await app_map[game_id](sub_scope, receive, send)

        return Mount("/game", app=game_dispatch)

    # ── Handler factories ───────────────────────────────────────────────

    def _make_index_handler(self, build: GameBuild):
        from starlette.responses import HTMLResponse

        async def handler(request):
            return HTMLResponse(self._render_index(build))
        return handler

    def _make_manifest_handler(self, build: GameBuild):
        from starlette.responses import JSONResponse

        async def handler(request):
            return JSONResponse(build.manifest)
        return handler

    def _make_sw_handler(self, build: GameBuild):
        from starlette.responses import Response

        async def handler(request):
            js = self._render_sw(build)
            return Response(js, media_type="application/javascript")
        return handler

    def _make_wasm_handler(self, build: GameBuild):
        from starlette.responses import FileResponse

        async def handler(request):
            wasm = build.build_dir / "index.wasm"
            if not wasm.exists():
                # Try common Godot export names
                for name in ("godot.wasm", "engine.wasm"):
                    wasm = build.build_dir / name
                    if wasm.exists():
                        break
            if not wasm.exists():
                from starlette.responses import JSONResponse
                return JSONResponse({"error": "engine.wasm not found"}, status_code=404)
            return FileResponse(
                str(wasm),
                media_type="application/wasm",
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                    "Access-Control-Allow-Origin": "*",
                },
            )
        return handler

    def _make_pck_handler(self, build: GameBuild):
        from starlette.responses import FileResponse, Response

        async def handler(request):
            pck = build.build_dir / "game.pck"
            if not pck.exists():
                for name in ("godot.pck", "main.pck"):
                    pck = build.build_dir / name
                    if pck.exists():
                        break
            if not pck.exists():
                from starlette.responses import JSONResponse
                return JSONResponse({"error": "game.pck not found"}, status_code=404)

            # Check for chunk request via query params
            chunk_n = request.query_params.get("chunk")
            if chunk_n is not None:
                return self._serve_chunk(pck, int(chunk_n), build.chunk_size)

            return FileResponse(
                str(pck),
                media_type="application/octet-stream",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                },
            )
        return handler

    def _make_chunk_handler(self, build: GameBuild):
        from starlette.responses import JSONResponse, Response

        async def handler(request):
            pck = build.build_dir / "game.pck"
            if not pck.exists():
                return JSONResponse({"error": "game.pck not found"}, status_code=404)

            chunk_n = request.path_params["chunk_n"]
            size_param = request.query_params.get("size")
            chunk_size = build.chunk_size
            if size_param:
                if size_param.endswith("K"):
                    chunk_size = int(size_param[:-1]) * 1024
                elif size_param.endswith("M"):
                    chunk_size = int(size_param[:-1]) * 1024 * 1024
                else:
                    chunk_size = int(size_param)

            return self._serve_chunk(pck, chunk_n, chunk_size)
        return handler

    def _serve_chunk(self, pck_path: Path, chunk_n: int, chunk_size: int) -> Response:
        from starlette.responses import Response

        file_size = pck_path.stat().st_size
        start = chunk_n * chunk_size
        end = min(start + chunk_size, file_size)

        if start >= file_size:
            return Response(b"", status_code=416)

        with open(pck_path, "rb") as f:
            f.seek(start)
            data = f.read(end - start)

        return Response(
            data,
            status_code=206,
            media_type="application/octet-stream",
            headers={
                "Content-Range": f"bytes {start}-{end - 1}/{file_size}",
                "Content-Length": str(len(data)),
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
            },
        )

    # ── Template renderers ──────────────────────────────────────────────

    def _render_index(self, build: GameBuild) -> str:
        s = build.splash
        logo_html = f'<img src="{s.logo_url}" class="logo" />' if s.logo_url else ""
        total_mb = build.manifest.get("total_size", 0) / (1024 * 1024)
        chunks = build.manifest.get("pck_chunks", 0)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{build.title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:{s.bg_color};color:{s.text_color};font-family:system-ui,sans-serif;
display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}}
#splash{{text-align:center;transition:opacity .5s}}
#splash.hidden{{opacity:0;pointer-events:none}}
.logo{{max-width:120px;margin-bottom:20px}}
h1{{font-size:1.8rem;margin-bottom:8px;font-weight:600}}
.subtitle{{font-size:.85rem;opacity:.6;margin-bottom:24px}}
.bar-bg{{width:280px;height:6px;background:rgba(255,255,255,.12);border-radius:3px;margin:0 auto 12px}}
.bar{{height:100%;width:0%;background:{s.accent_color};border-radius:3px;transition:width .2s}}
.status{{font-size:.78rem;opacity:.5}}
#game-canvas{{position:fixed;top:0;left:0;width:100%;height:100%;display:none;z-index:1}}
</style>
</head>
<body>
<div id="splash">
  {logo_html}
  <h1>{build.title}</h1>
  <p class="subtitle">{s.subtitle}</p>
  <div class="bar-bg"><div class="bar" id="bar"></div></div>
  <p class="status" id="status">Preparing...</p>
</div>
<canvas id="game-canvas"></canvas>
<script>
const GAME_ID="{build.game_id}";
const TOTAL_MB={total_mb:.1f};
const CHUNKS={chunks};
const CHUNK_SIZE={build.chunk_size};
let loaded=0,total=0;

function update(pct,msg){{
  document.getElementById("bar").style.width=pct+"%";
  document.getElementById("status").textContent=msg;
}}

async function load(){{
  try{{await navigator.serviceWorker.register("/sw.js")}}catch(e){{}}

  let manifest;
  try{{
    const r=await fetch("/manifest.json");
    manifest=await r.json();
  }}catch(e){{manifest={{files:{{}},total_size:0,pck_chunks:0}}}}

  total=(manifest.total_size||0)/(1024*1024);
  update(0,"Loading engine...");

  // Load engine.wasm
  const wasmResp=await fetch("/engine.wasm");
  const wasmBytes=await wasmResp.arrayBuffer();
  update(40,"Engine loaded. Loading game data...");

  // Load game.pck in chunks
  let pckBytes=[];
  const pckChunks=manifest.pck_chunks||1;
  for(let i=0;i<pckChunks;i++){{
    const r=await fetch(`/chunk/${{i}}`);
    const buf=await r.arrayBuffer();
    pckBytes.push(new Uint8Array(buf));
    const pct=40+Math.round((i+1)/pckChunks*55);
    update(pct,`Game data ${{Math.round((i+1)/pckChunks*100)}}%...`);
  }}

  // Merge pck chunks
  let totalLen=0;
  for(const c of pckBytes) totalLen+=c.length;
  const merged=new Uint8Array(totalLen);
  let offset=0;
  for(const c of pckBytes){{merged.set(c,offset);offset+=c.length;}}

  update(98,"Starting game...");

  // Start Godot engine
  const canvas=document.getElementById("game-canvas");
  canvas.style.display="block";
  document.getElementById("splash").classList.add("hidden");

  // Standard Godot loader integration
  if(typeof createGodotEngine==="function"){{
    createGodotEngine(canvas,{{
      executable: "/engine.wasm",
      pckData: merged,
    }});
  }}else if(window.Godot){{
    // Fallback: use standard Godot load
    const engine=new Godot();
    engine.setCanvas(canvas);
    await engine.start({{executable:"/engine.wasm",pck:merged}});
  }}
}}

load();
</script>
</body>
</html>"""

    def _render_sw(self, build: GameBuild) -> str:
        version = build.manifest.get("files", {}).get("game.pck", {}).get("hash", "v1")
        return f"""// EVOID Game Service Worker — {build.game_id}
const CACHE="evoid-{build.game_id}-{version}";
const PRECACHE=[
  "/",
  "/engine.js",
  "/engine.wasm",
  "/manifest.json",
];

self.addEventListener("install",e=>{{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(PRECACHE)).then(()=>self.skipWaiting()));
}});

self.addEventListener("activate",e=>{{
  e.waitUntil(caches.keys().then(ks=>Promise.all(
    ks.filter(k=>k!==CACHE).map(k=>caches.delete(k))
  )).then(()=>self.clients.claim()));
}});

self.addEventListener("fetch",e=>{{
  const url=new URL(e.request.url);
  const path=url.pathname;

  // engine.wasm, engine.js — cache-first, immutable
  if(path==="/engine.wasm"||path==="/engine.js"){{
    e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
    return;
  }}

  // chunks — network-first
  if(path.startsWith("/chunk/")){{
    e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
    return;
  }}

  // game.pck — stale-while-revalidate
  if(path==="/game.pck"){{
    e.respondWith(caches.open(CACHE).then(c=>{{
      return c.match(e.request).then(r=>{{
        const fetchPromise=fetch(e.request).then(resp=>{{
          c.put(e.request,resp.clone());return resp;
        }});
        return r||fetchPromise;
      }});
    }}));
    return;
  }}

  // assets/* — cache-first
  if(path.startsWith("/assets/")){{
    e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
    return;
  }}

  // everything else — network
}});"""
