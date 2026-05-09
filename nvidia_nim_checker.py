#!/usr/bin/env python3
# ──────────────────────────────────────────────
#  NVIDIA NIM — Model Access Checker
#  Checks which models are accessible with your
#  NVIDIA API key by sending a minimal test request
#  to each model and reporting the result.
#
#  Usage:
#    python nvidia_nim_checker.py
#    python nvidia_nim_checker.py --key nvapi-xxxx
# ──────────────────────────────────────────────

import sys
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL    = "https://integrate.api.nvidia.com/v1"
MAX_WORKERS   = 10
MAX_RETRIES   = 5
RETRY_BACKOFF = 2  # seconds — doubles on each retry

STATUS_LABELS = {
    200: ("✅", "ACCESSIBLE"),
    402: ("💳", "CREDITS EXHAUSTED"),
    403: ("🔒", "NO ACCESS"),
    404: ("❌", "NOT FOUND"),
    422: ("⚙️ ", "DIFFERENT TYPE (e.g. embedding)"),
}


def fetch_model_ids() -> list[str]:
    response = requests.get(f"{BASE_URL}/models", timeout=10)
    response.raise_for_status()
    return [m["id"] for m in response.json().get("data", [])]


def test_model(model_id: str, api_key: str) -> tuple[str, str, str, int]:
    import time

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":    model_id,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 1,
        "stream":   False,
    }

    delay = RETRY_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,
            )

            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", delay))
                time.sleep(retry_after)
                delay *= 2
                continue

            icon, label = STATUS_LABELS.get(r.status_code, ("?", f"UNKNOWN ({r.status_code})"))
            return model_id, icon, label, r.status_code

        except requests.exceptions.Timeout:
            return model_id, "⏱️ ", "TIMEOUT", 0
        except Exception as e:
            return model_id, "💥", f"ERROR: {e}", -1

    return model_id, "⏳", f"RATE LIMITED (gave up after {MAX_RETRIES} retries)", 429


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check which NVIDIA NIM models are accessible with your API key."
    )
    parser.add_argument(
        "--key", "-k",
        metavar="API_KEY",
        help="Your NVIDIA API key (nvapi-...)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print()
    print("╔══════════════════════════════════════════════╗")
    print("║       NVIDIA NIM — Model Access Checker      ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    api_key = args.key or input("Enter your API key (nvapi-...): ").strip()

    if not api_key.startswith("nvapi-"):
        print("\n  [!] API key must start with 'nvapi-'")
        sys.exit(1)

    print("\n  Fetching model list...")
    try:
        models = fetch_model_ids()
    except Exception as e:
        print(f"\n  [!] Failed to fetch models: {e}")
        sys.exit(1)

    print(f"  {len(models)} models found.")
    print(f"\n  Testing access (up to {MAX_WORKERS} parallel requests)...\n")
    print(f"  {'MODEL':<55} {'STATUS'}")
    print(f"  {'─' * 55} {'─' * 25}")

    results: dict[int, list[str]] = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(test_model, m, api_key): m for m in models}
        for future in as_completed(futures):
            model_id, icon, label, code = future.result()
            print(f"  {model_id:<55} {icon} {label}")
            results.setdefault(code, []).append(model_id)

    # ── Summary ───────────────────────────────────
    accessible = results.get(200, [])
    no_access  = results.get(403, [])

    print()
    print("╔══════════════════════════════════════════════╗")
    print("║                    SUMMARY                   ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    print(f"  ✅  Accessible      : {len(accessible)}")
    print(f"  🔒  No access       : {len(no_access)}")
    print(f"  ⚙️   Other / unknown : {len(models) - len(accessible) - len(no_access)}")

    if accessible:
        print()
        print("  ── Models you can use ──────────────────────")
        for m in sorted(accessible):
            print(f"     • {m}")

    print()


if __name__ == "__main__":
    main()