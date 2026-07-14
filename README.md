# sesame agent

sesame agent is an agent you can put to work. Give it a task in your terminal or
your browser and it goes and does it: reads and edits your files, runs commands,
searches the web, drives a real browser, and shows you its thinking as it goes.

## It does not forget what it was thinking

An agent thinks, calls a tool, reads the result, and thinks again. Between those
steps its reasoning is usually thrown away: the model gets its own tool calls back,
but not the thinking that produced them. So at every step it reconstructs why it was
doing this, from the evidence, like walking into a room and having to work out what
you came in for.

sesame agent hands the reasoning back with the next request, on both wires, so the
model is still holding what it worked out.

You can watch the difference. The model picks a number inside its reasoning, never
says it out loud, calls a tool, and is then asked what the number was. It cannot
work it out again, so either it can see its earlier thinking or it is guessing:

```bash
python3 test/reasoning.py 5
```

```
reasoning carried back:      recalled its own reasoning 5/5
reasoning dropped:           recalled its own reasoning 1/5   (one lucky guess)
```

That is the whole idea. Everything else here (undo, permissions that only stop what
you cannot take back, sessions, memory, a sub agent, a browser, a terminal and a web
interface on the same core) exists to make it a thing you can actually work with.

**Using a coding agent?** Give it [SETUP.md](SETUP.md) and it will install,
configure and launch this for you:

```
install https://github.com/vcup-date/sesame-agent by following its SETUP.md
```

Doing it yourself:

```bash
git clone https://github.com/vcup-date/sesame-agent && cd sesame-agent
./run.sh
```

First run installs what it needs and sets up a model.

![a turn](docs/hero.png)

## In a browser

```bash
./run.sh web            # http://127.0.0.1:9981
```

The same core, the same tools, the same session files. It is not a terminal being
scraped: the web server drives the agent directly.

![the web interface](docs/web.png)

Streaming reasoning you can open, tool calls with their output and diffs,
permission prompts with allow once / always / deny, steering while it works,
sessions, undo, and every setting in one place: provider, key, model, your own
endpoint, profiles, effort, permissions, working folder, theme and text size.

When the model is local and its server reports progress (llama.cpp does), the
status line shows the context being read, the rate, and how much of the prompt was
served from cache, instead of a spinner.

![settings](docs/web-settings.png)

## Lightweight and fast

Pure Python. One required dependency. 20 files, 5.4k lines. Startup is about
70ms and it holds around 45MB.

`shell.py` is the engine. It owns the wire, retries, the safety gate and the token
ceiling. It does not plan, does not decide what to do next, and does not know what
task it is running. The model does that, and it keeps its reasoning while it does:
thinking blocks go back verbatim with every request, with the interleaved-thinking
beta on the Anthropic wire and `reasoning_content` on the OpenAI one. A server that
refuses the field is remembered, and gets the plain shape instead.

## Web and browser

It is not limited to code. It fetches pages, searches the web, and drives
Chromium through pages, logins and forms.

![out on the web](docs/research.png)

## Steering

Type while it works. Your message reaches the model at its next step and it
changes course, keeping what it has already done.

![steering a running turn](docs/steer.png)

## Permissions and undo

Writing files, editing code, running your tests: it does those without asking. It
stops for `rm -rf`, `sudo`, force pushes, publishing, overwriting a file that
already exists, touching a `.env`, writing outside your project, `curl | sh`.

![the permission prompt](docs/permission.png)

Approvals are remembered per project. `/undo` reverts a turn: every file is
snapshotted before it is touched.

## Models and profiles

![the model picker](docs/model.png)

The model list is fetched from the provider, not hardcoded, so it also shows what
your own Ollama has pulled. A profile stores a full setup under one name:
endpoint, protocol, model, key, context window, effort.

| | |
|---|---|
| hosted | deepseek, anthropic, openai, openrouter, groq, xai, mistral, together |
| local | Ollama, LM Studio, llama.cpp, vLLM, MLX, any OpenAI or Anthropic compatible URL |

Local models need no key. sesame agent asks the server for its context window
instead of assuming one, so a 256k model you serve yourself is used as 256k, and
it is not sent a `reasoning_effort` it has no answer for.

`SESAME_PROFILE=local ./run.sh` runs one session on a profile without changing
your saved setup.

## Effort

![the effort slider](docs/effort.png)

## Sessions, tools, retries

Sessions are one jsonl file each in `.sesame/sessions/`. `/resume` replays a
session as it happened, tool output and reasoning included.

Tools: read, write, edit, ripgrep search, shell, web fetch, web search, browser
(navigate, click, type, screenshot), a sub agent for exploration that keeps raw
file dumps out of your context, and a memory that persists across sessions. An
`AGENTS.md` in your project (`/init` writes one) is loaded every session.

Rate limits, 5xx and network drops are retried with backoff and honour
`Retry-After`; the turn continues where it stopped. A server that is not
listening is reported in about three seconds instead of being retried five times.

## Commands

```
/model         switch model, or use your own      /provider   switch provider
/undo          revert its file edits              /tools      what it can do
/compact       free up context                    /effort     how hard it thinks
/think         show the full reasoning            /memory     what it remembers
/save /resume  sessions                           /sessions   list them
/permissions   what it may do unasked             /confirm    approval prompts
/init          write an AGENTS.md                 /copy /clear /help /quit
```

| key | |
|---|---|
| `enter` | send, or steer it while it works |
| `esc` | stop the current turn |
| `ctrl-t` | show or hide the full reasoning |
| `ctrl-y` | copy the last answer |
| `tab` | complete a command |

## Headless

```bash
./run.sh --print "summarize the diff on this branch"
./run.sh --print "fix the failing test" --dangerously-skip-permissions
./run.sh --resume refactor-auth
```

Without that flag, a headless run cannot modify anything.

## Doctor

```bash
./run.sh doctor         # what is wrong
./run.sh doctor --fix   # fix what can be fixed
```

It checks Python, the dependency, your key, whether the endpoint answers, whether
each profile's server is up, and whether it can write to `.sesame/`.

## Configuration

`.env`, then `~/.sesame/config.json`, then `.sesame/config.json`, then the
environment. Keys: `model`, `baseUrl`, `wire`, `apiKey`, `effort`,
`contextWindow`, `confirmDanger`, `toolCallBudget`. `SESAME_LOG=/tmp/sesame.log`
writes a debug log with the API key redacted.

## Development

```bash
python3 test/units.py        # 176 offline tests, no network
python3 test/smoke.py        # against the live API
```

`shell.py` talks to the model and runs its tools. `loop.py` holds the
conversation, permissions and undo history. `cli.py` is the interface. `tools.py`,
`browser.py` and `subagent.py` are what the agent can do. The core is stdlib.
`prompt_toolkit` draws the prompt. `playwright` is optional, for the browser.

MIT.
