"""Smoke público limitado a HTTP 200 e JSON saudável; não chama IA."""
import json
import sys
import time
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_health(url: str, attempts: int = 6, delay: float = 5, timeout: float = 10) -> bool:
    opener = build_opener(NoRedirect())
    for attempt in range(attempts):
        try:
            with opener.open(url, timeout=timeout) as response:
                if response.status == 200 and json.load(response) == {"status": "healthy"}:
                    print("Public /health: HTTP 200 and healthy JSON")
                    return True
        except (URLError, OSError, ValueError):
            # Não inclui corpos de resposta ou dados de autenticação nos logs.
            pass
        print(f"Health check attempt {attempt + 1}/{attempts} failed", file=sys.stderr)
        if attempt + 1 < attempts:
            time.sleep(delay)
    return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 scripts/ci/public_health.py HEALTH_URL")
    sys.exit(0 if check_health(sys.argv[1]) else 1)
