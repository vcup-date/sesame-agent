# SETUP.md

Instructions for a coding agent installing sesame agent for its user. Follow them
in order. Every command is meant to be run as written.

## What you are installing

sesame agent: a terminal and browser agent in Python. It needs Python 3.10 or
newer, and a model to talk to (a hosted API key, or a local server).

## 1. Get the code

```bash
git clone https://github.com/vcup-date/sesame-agent
cd sesame-agent
```

## 2. Check Python

```bash
python3 --version      # 3.10 or newer
```

If it is older, stop and tell the user to install Python 3.10+. Do not try to
upgrade their system Python yourself.

## 3. Give it a model

sesame agent reads `.env` in the project, so this is the whole configuration
step. Pick ONE of the following.

**A hosted model.** Ask the user for their API key. Do not invent one, do not
reuse a key you find elsewhere on the machine, and do not print it back to them.

```bash
# deepseek (default endpoint, no other setting needed)
printf 'SESAME_API_KEY=%s\n' "THE_KEY_THE_USER_GAVE_YOU" > .env
```

For another provider, set the endpoint and protocol too:

```bash
printf 'SESAME_API_KEY=%s\nSESAME_BASE_URL=%s\nSESAME_MODEL=%s\nSESAME_WIRE=%s\n' \
  "THE_KEY" "https://api.anthropic.com" "claude-sonnet-5" "anthropic" > .env
```

`SESAME_WIRE` is `anthropic` or `openai`, and it describes the protocol, not the
vendor. OpenAI, OpenRouter, Groq, xAI, Mistral and Together all speak `openai`.

**A local model.** No key is needed. Point it at the server:

```bash
printf 'SESAME_BASE_URL=%s\nSESAME_MODEL=%s\nSESAME_WIRE=openai\n' \
  "http://127.0.0.1:11434/v1" "qwen3-coder" > .env
```

Common local endpoints: Ollama `http://127.0.0.1:11434/v1`, LM Studio
`http://127.0.0.1:1234/v1`, llama.cpp `http://127.0.0.1:8080/v1`. The context
window is read from the server, so do not guess one.

## 4. Install and verify

```bash
./run.sh doctor
```

The first run creates a virtualenv and installs the one dependency. Expect it to
end with `everything checks out`. It checks Python, the dependency, the key,
whether the endpoint answers, and whether it can write to `.sesame/`.

If it reports a problem, fix that problem and run it again. `./run.sh doctor --fix`
installs what it can (ripgrep, playwright).

## 5. Hand it over

```bash
./run.sh          # the terminal interface
./run.sh web      # the browser interface, http://127.0.0.1:9981
```

Tell the user both commands exist, and that `./run.sh doctor` is what to run when
something breaks.

## Optional

Browser tools (a real Chromium: navigate, click, type, screenshot):

```bash
.venv/bin/pip install playwright && .venv/bin/playwright install chromium
```

Faster search, if `rg` is not already installed:

```bash
brew install ripgrep       # macOS
sudo apt install ripgrep   # Debian, Ubuntu
```

## Rules

- Never commit `.env` or `.sesame/`. Both are already in `.gitignore`. Leave them
  that way.
- Never print the user's API key, and never write it anywhere except `.env` or
  `~/.sesame/config.json`.
- Do not edit files under `.sesame/`. That is the user's sessions, undo history
  and permissions.
- If the user has no key and no local server, stop and ask. Do not sign them up
  for anything.

## Verify it actually works

```bash
echo "reply with the single word READY. no tools." | ./run.sh
```

That prints a line of output ending in `READY`. If it does, the install is done.
