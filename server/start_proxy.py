"""
start_proxy.py — starts mitmproxy with the guardian_http addon.

Usage:
    python server/start_proxy.py

Environment variables:
    GUARDIAN_HTTP_LISTEN_PORT          — proxy listen port (default: 8080)
    GUARDIAN_HTTP_MONITORED_CLIENT_IP  — IP to monitor (default: 100.73.141.11)

The child device must:
    1. Set its HTTP/HTTPS proxy to <this-machine-IP>:<GUARDIAN_HTTP_LISTEN_PORT>
    2. For HTTPS: install ~/.mitmproxy/mitmproxy-ca-cert.pem as a trusted root CA
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Allow running from repo root or from server/
sys.path.insert(0, str(Path(__file__).resolve().parent))

LISTEN_PORT = int(os.getenv("GUARDIAN_HTTP_LISTEN_PORT", "8080"))


async def _run() -> None:
    try:
        from mitmproxy.options import Options
        from mitmproxy.tools.dump import DumpMaster
    except ImportError:
        print("[start_proxy] mitmproxy is not installed. Run: pip install mitmproxy")
        sys.exit(1)

    from guardian_http import GuardianHTTPAddon

    opts = Options(listen_host="0.0.0.0", listen_port=LISTEN_PORT)
    master = DumpMaster(opts, with_termlog=False, with_dumper=False)
    master.addons.add(GuardianHTTPAddon())

    print(f"[Guardian HTTP Proxy] Listening on 0.0.0.0:{LISTEN_PORT}")
    print(f"[Guardian HTTP Proxy] Logging to server/logs/http_log.json")
    print(f"[Guardian HTTP Proxy] Press Ctrl+C to stop")

    try:
        await master.run()
    except KeyboardInterrupt:
        master.shutdown()


if __name__ == "__main__":
    asyncio.run(_run())
