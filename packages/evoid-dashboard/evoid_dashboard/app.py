"""Dashboard ASGI app — lightweight monitoring UI."""

from __future__ import annotations

import json
from typing import Any

from .collectors import (
    collect_services,
    collect_intents,
    collect_processors,
    collect_message_history,
    collect_db_tables,
    collect_pipeline_overrides,
    collect_system_info,
)


async def app(scope: dict, receive: Any, send: Any) -> None:
    """ASGI app for the dashboard."""
    if scope["type"] != "http":
        return

    path = scope.get("path", "/")
    method = scope.get("method", "GET")

    # Route
    if path == "/" or path == "":
        body = _render_index()
    elif path == "/api/services":
        body = _json(collect_services())
    elif path == "/api/intents":
        body = _json(collect_intents())
    elif path == "/api/processors":
        body = _json(collect_processors())
    elif path == "/api/messages":
        body = _json(collect_message_history())
    elif path == "/api/databases":
        body = _json(collect_db_tables())
    elif path == "/api/pipelines":
        body = _json(collect_pipeline_overrides())
    elif path == "/api/system":
        body = _json(collect_system_info())
    elif path == "/api/all":
        # Fetch registry data once, pass to collectors
        from evoid import all_intents, all_processors
        intents = all_intents()
        processors = all_processors()
        body = _json({
            "services": collect_services(intents, processors),
            "intents": collect_intents(intents),
            "processors": collect_processors(processors),
            "messages": collect_message_history(),
            "databases": collect_db_tables(),
            "pipelines": collect_pipeline_overrides(),
            "system": collect_system_info(),
        })
    else:
        body = b'{"error": "not found"}'
        await _send_response(send, 404, body, "application/json")
        return

    content_type = "text/html" if path in ("/", "") else "application/json"
    await _send_response(send, 200, body, content_type)


def _json(data: Any) -> bytes:
    return json.dumps(data, default=str, ensure_ascii=False).encode()


async def _send_response(send: Any, status: int, body: bytes, content_type: str) -> None:
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            [b"content-type", content_type.encode()],
            [b"content-length", str(len(body)).encode()],
            [b"access-control-allow-origin", b"*"],
        ],
    })
    await send({"type": "http.response.body", "body": body})


def _render_index() -> bytes:
    """Render the dashboard HTML."""
    return DASHBOARD_HTML.encode()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EVOID Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui; background: #0a0a0a; color: #e0e0e0; }
.header { padding: 20px; background: #111; border-bottom: 1px solid #333; }
.header h1 { font-size: 24px; color: #fff; }
.header p { color: #888; margin-top: 4px; }
.tabs { display: flex; gap: 0; padding: 0 20px; background: #111; border-bottom: 1px solid #333; }
.tab { padding: 12px 20px; cursor: pointer; color: #888; border-bottom: 2px solid transparent; }
.tab:hover { color: #fff; }
.tab.active { color: #fff; border-bottom-color: #7c3aed; }
.content { padding: 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.card { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 16px; }
.card h3 { color: #7c3aed; margin-bottom: 8px; font-size: 14px; }
.card .value { font-size: 28px; font-weight: bold; color: #fff; }
.card .label { color: #888; font-size: 12px; margin-top: 4px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #333; }
th { color: #888; font-size: 12px; text-transform: uppercase; }
td { color: #e0e0e0; font-size: 14px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
.badge-green { background: #065f46; color: #6ee7b7; }
.badge-yellow { background: #78350f; color: #fcd34d; }
.badge-red { background: #7f1d1d; color: #fca5a5; }
.badge-blue { background: #1e3a5f; color: #93c5fd; }
.hidden { display: none; }
.node { padding: 12px; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; display: inline-block; margin: 8px; }
.node .name { font-weight: bold; color: #7c3aed; }
.node .type { color: #888; font-size: 12px; }
#refresh { background: #7c3aed; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
</style>
</head>
<body>
<div class="header">
  <h1>EVOID Dashboard</h1>
  <p>Service map, data lineage, database viewer, live logs</p>
</div>

<div class="tabs">
  <div class="tab active" onclick="showTab('overview')">Overview</div>
  <div class="tab" onclick="showTab('services')">Services</div>
  <div class="tab" onclick="showTab('intents')">Intents</div>
  <div class="tab" onclick="showTab('messages')">Messages</div>
  <div class="tab" onclick="showTab('databases')">Databases</div>
  <div class="tab" onclick="showTab('system')">System</div>
</div>

<div class="content">
  <!-- Overview -->
  <div id="tab-overview">
    <div class="grid" id="stats"></div>
    <h2 style="margin: 20px 0 12px; color: #fff;">Service Map</h2>
    <div id="service-map"></div>
  </div>

  <!-- Services -->
  <div id="tab-services" class="hidden">
    <h2 style="margin-bottom: 12px; color: #fff;">Registered Services</h2>
    <table id="services-table">
      <thead><tr><th>Service</th><th>Intents</th><th>Processors</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <!-- Intents -->
  <div id="tab-intents" class="hidden">
    <h2 style="margin-bottom: 12px; color: #fff;">All Intents</h2>
    <table id="intents-table">
      <thead><tr><th>Name</th><th>Level</th><th>Timeout</th><th>Priority</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <!-- Messages -->
  <div id="tab-messages" class="hidden">
    <h2 style="margin-bottom: 12px; color: #fff;">Message Bus History</h2>
    <table id="messages-table">
      <thead><tr><th>Source</th><th>Intent</th><th>Target</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <!-- Databases -->
  <div id="tab-databases" class="hidden">
    <h2 style="margin-bottom: 12px; color: #fff;">Database Connections</h2>
    <div id="db-list" class="grid"></div>
  </div>

  <!-- System -->
  <div id="tab-system" class="hidden">
    <h2 style="margin-bottom: 12px; color: #fff;">System Info</h2>
    <div id="system-info" class="card"></div>
  </div>
</div>

<script>
let data = {};

async function refresh() {
  const res = await fetch('/api/all');
  data = await res.json();
  render();
}

function render() {
  // Stats
  document.getElementById('stats').innerHTML = `
    <div class="card"><h3>Services</h3><div class="value">${data.services?.length || 0}</div></div>
    <div class="card"><h3>Intents</h3><div class="value">${data.intents?.length || 0}</div></div>
    <div class="card"><h3>Processors</h3><div class="value">${data.processors?.length || 0}</div></div>
    <div class="card"><h3>Messages</h3><div class="value">${data.messages?.length || 0}</div></div>
  `;

  // Service map
  let mapHtml = '';
  (data.services || []).forEach(s => {
    mapHtml += `<div class="node"><div class="name">${s.name}</div><div class="type">${s.intents?.length || 0} intents, ${s.processors?.length || 0} processors</div></div>`;
  });
  document.getElementById('service-map').innerHTML = mapHtml || '<p style="color:#888">No services registered</p>';

  // Services table
  const sBody = document.querySelector('#services-table tbody');
  sBody.innerHTML = (data.services || []).map(s => `<tr><td>${s.name}</td><td>${s.intents?.length || 0}</td><td>${s.processors?.length || 0}</td></tr>`).join('');

  // Intents table
  const iBody = document.querySelector('#intents-table tbody');
  iBody.innerHTML = (data.intents || []).map(i => `<tr><td>${i.name}</td><td><span class="badge badge-${i.level==='critical'?'red':i.level==='ephemeral'?'yellow':'green'}">${i.level}</span></td><td>${i.timeout || 'default'}</td><td>${i.priority || 0}</td></tr>`).join('');

  // Messages table
  const mBody = document.querySelector('#messages-table tbody');
  mBody.innerHTML = (data.messages || []).map(m => `<tr><td>${m.source}</td><td>${m.intent}</td><td>${m.target || '-'}</td></tr>`).join('') || '<tr><td colspan="3" style="color:#888">No messages yet</td></tr>';

  // Databases
  document.getElementById('db-list').innerHTML = Object.entries(data.databases || {}).map(([name, tables]) => `<div class="card"><h3>${name}</h3><div class="value">${tables.length}</div><div class="label">engines</div></div>`).join('') || '<p style="color:#888">No databases connected</p>';

  // System
  const sys = data.system || {};
  document.getElementById('system-info').innerHTML = `<p><strong>Python:</strong> ${sys.python || '?'}</p><p><strong>EVOID:</strong> ${sys.evoid_version || '?'}</p><p><strong>Platform:</strong> ${sys.platform || '?'}</p>`;
}

function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('[id^="tab-"]').forEach(t => t.classList.add('hidden'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.remove('hidden');
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""


def create_dashboard(host: str = "0.0.0.0", port: int = 8001):
    """Create the dashboard ASGI app. Returns the ASGI app object."""
    return app


def run_dashboard(host: str = "0.0.0.0", port: int = 8001) -> None:
    """Run the dashboard ASGI server (blocking)."""
    import uvicorn
    print(f"EVOID Dashboard: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
