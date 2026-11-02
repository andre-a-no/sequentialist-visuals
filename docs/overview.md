# Understand sequentialist-visuals

English · [Русский](overview.ru.md)

## What is it for?

`sequentialist-visuals` turns supplied search or interaction records into a
portable HTML page. Open that page in a browser to inspect a diagram and the
complete textual records. It is part of the ecosystem's engineering platform;
it does not perform the mathematical search or make application decisions.

Two views are implemented:

| Question | Input | Output |
|---|---|---|
| What premises and rules lead to a conclusion? | Nodes and rules, including AND-premises and OR-alternatives | Search/provenance diagram plus state and rule records |
| What happened to each participant? | Timestamped events, participant names and optional explicit causes | Participant lanes plus an event table |

Use this package when records already exist and need to be inspected or shared.
Use `sequential-search` for the algorithms that construct a solution, or
`sequential-games` for mathematical interaction models. Domain applications
provide the subject meaning of goals, events and actions.

## First workflow without programming

1. Read the [README examples](../README.md) and choose a search view or timeline.
2. Collect a small list of states/rules or participant events. State what an
   identifier, time and status mean in your application.
3. Ask a developer or assistant to map those records to the documented schema
   and run `render_search` or `render_timeline`.
4. Open the generated HTML file in a browser. The page works offline and contains
   the complete supplied records alongside the drawing.
5. Inspect the sources and interpretation of those records before relying on
   their conclusions. A diagram does not validate its content.

There is no hosted service or graphical data-entry interface in this version.
Python is needed to generate a page; viewing an already generated page needs
only a browser. An assistant may help prepare the input, but the renderer does
not contact an AI service.

## Developer workflow

Run these commands from the repository root:

```bash
python -m pip install -e .
```

Then use either complete [README example](../README.md) to write an HTML file.
`render_search(graph, title=...)` and `render_timeline(events, title=...)` return
strings. File output is an explicit caller action. The functions do not mutate
inputs or start a server.

The adjacent [sequentialist-agentic repository](https://github.com/andre-a-no/sequentialist-agentic)
has a development example in `examples/reasoning_demo.py` that uses this API.
That integration requires matching development versions of agentic and search;
new local examples are not necessarily available in the published branch yet.

## Input rules that matter

- Search nodes have unique string IDs. Every premise and conclusion references
  a supplied node. All premises of one rule form an AND group; separate rules
  for the same conclusion are alternatives.
- Status labels are supplied by the caller and displayed as text. The renderer
  does not promote a label such as `derived` into a verified proof.
- Timeline event IDs are unique strings. Times are finite numbers on a
  caller-defined common scale. A cause must reference a supplied event and
  cannot occur later than its effect on that scale.
- Equal timestamps and neighboring rows do not establish a causal order. Only
  explicit cause links draw causal arrows. Input row order is preserved.
- Payloads use finite JSON values. Labels and payloads are escaped as text in
  the output; they are not executed as HTML or JavaScript.

The exact schemas and examples are in [README.md](../README.md). Validation
behavior is exercised by [test_render.py](../tests/test_render.py).

## Current capabilities and planned boundaries

Implemented: bounded standalone HTML/SVG views, escaped text, graph-reference
checks, cyclic-graph display notices, explicit event-causality checks, caller
order preservation and offline output.

A live dashboard, editing application state, semantic proof checking, statistical
calibration, distributed-clock reconciliation and operational audit verification
are not implemented. No delivery date is implied. They should not be inferred
from a successful render.

## FAQ

**Does a rendered proof establish that the conclusion is true?**
No. The page displays the supplied premises and rules. A separate validator and
sound subject rules are needed. A finite symbolic proof example is not a
general mathematical or olympiad problem solver.

**Does a chart establish a statistical guarantee?**
No. Statistical guarantees come from the underlying method and its assumptions.
This renderer neither computes them nor checks an LLM evaluator's calibration.

**Can I use it with data from another program?**
Yes, after mapping that program's records to the documented schema. There is no
mandatory dependency on other Sequentialist packages.

**Can Codex, Claude, Qwen, Gemini, Grok or Perplexity read these docs?**
They can use documentation they are able and permitted to access. Some coding
clients recognize particular instruction files; behavior depends on the client
and configuration. Give the assistant the [overview](overview.md),
[README](../README.md) or [reading index](../llms.txt) explicitly when needed.
Grok and Perplexity may consume accessible web documentation; this repository
does not promise crawling, indexing, citation or ranking by any service.

## Source of truth

- [Package metadata](../pyproject.toml): installation name and Python requirement.
- [Public exports](../src/sequentialist/visuals/__init__.py): callable API.
- [Renderer](../src/sequentialist/visuals/render.py): exact behavior.
- [Tests](../tests/test_render.py): executable contract examples.
- [Repository guidance](../AGENTS.md): source map and check commands.
