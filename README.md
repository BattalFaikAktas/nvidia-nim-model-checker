# nvidia-nim-model-checker

Check which NVIDIA NIM models are accessible with your API key.

---

## Requirements

- Python 3.11+
- An NVIDIA NIM API key → [build.nvidia.com](https://build.nvidia.com)

---

## Usage

### Python

```bash
pip install -r requirements.txt
python nvidia_nim_checker.py
```

Or pass your key directly:

```bash
python nvidia_nim_checker.py --key nvapi-xxxx
```

### Docker

No build required:

```bash
docker run --rm -it python:3.11 bash -c "
  pip install requests -q &&
  python -c \"import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/BattalFaikAktas/nvidia-nim-model-checker/main/nvidia_nim_checker.py', 'nvidia_nim_checker.py')\" &&
  python nvidia_nim_checker.py --key nvapi-xxxx
"
```

---

## Output

```
╔══════════════════════════════════════════════╗
║       NVIDIA NIM — Model Access Checker      ║
╚══════════════════════════════════════════════╝

  Fetching model list...
  142 models found.

  Testing access (up to 10 parallel requests)...

  MODEL                                                   STATUS
  ─────────────────────────────────────────────────────── ─────────────────────────
  meta/llama-3.1-8b-instruct                              ✅ ACCESSIBLE
  meta/llama-3.1-70b-instruct                             ✅ ACCESSIBLE
  deepseek-ai/deepseek-r1                                 ✅ ACCESSIBLE
  mistralai/mistral-7b-instruct-v0.3                      🔒 NO ACCESS
  ...

╔══════════════════════════════════════════════╗
║                    SUMMARY                   ║
╚══════════════════════════════════════════════╝

  ✅  Accessible      : 12
  🔒  No access       : 128
  ⚙️   Other / unknown : 2

  ── Models you can use ──────────────────────
     • deepseek-ai/deepseek-r1
     • meta/llama-3.1-8b-instruct
     • meta/llama-3.1-70b-instruct
     ...
```

---

## How it works

1. Fetches the full model list from the public NVIDIA NIM endpoint
2. Sends a minimal test request (`max_tokens: 1`) to each model using your API key
3. Reports the result for each model based on the HTTP response code

| Status | Meaning |
|---|---|
| ✅ ACCESSIBLE | Model is available with your key |
| 🔒 NO ACCESS | Your key does not have access |
| 💳 CREDITS EXHAUSTED | Free credits have run out |
| ⚙️ DIFFERENT TYPE | Not a chat model (e.g. embedding) |
| ⏱️ TIMEOUT | Model did not respond in time |

> Rate limited requests (429) are automatically retried with exponential backoff.

---

## License

MIT