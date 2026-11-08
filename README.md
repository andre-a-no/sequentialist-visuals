# sequentialist-visuals

Read-only engineering views of search provenance and participant events. This
package belongs to the reusable software-engineering layer of the Sequentialist
ecosystem. It displays supplied records without running searches, changing
decisions or inferring statistical guarantees or proof validity.

Python 3.11+, standard-library runtime only. Generated pages contain standalone
HTML, SVG and CSS; they work offline with no JavaScript, CDN, server or network
requests. Labels, identifiers and JSON data are escaped as text.

## Conceptual framework: the Sequentialist ecosystem

The ecosystem studies sequential decisions: observations arrive, evidence
changes, and a policy chooses whether to continue, act, wait or stop. It separates
three questions within the mathematical and cybernetic methods layer:

| Library | Central question | Responsibility |
|---|---|---|
| [sequential-analysis](https://github.com/andre-a-no/sequential-analysis) | What can we infer from the observations available so far? | Statistical tests, estimation, filtering, prediction and procedure-specific uncertainty guarantees. |
| [sequential-search](https://github.com/andre-a-no/sequential-search) | Which step should we explore next to reach an answer or a goal? | Search and reasoning over alternatives, experiments and rules, with explicit evidence, provenance and resource costs. |
| [sequential-games](https://github.com/andre-a-no/sequential-games) | How do participants pursue their own goals while their actions change a shared environment? | Interaction models for cooperation, competition and partially aligned interests, including asynchronous actions, local information and deliberate waiting. |

These are complementary responsibilities. A participant's policy can use search
to plan and statistical analysis to interpret observations; other participants
continue to act according to their own objectives. This describes how the
methods can be composed. Each package's implementation status is stated
separately below.

The naming convention expresses a further separation into three layers:

| Layer | Packages | Responsibility |
|---|---|---|
| Mathematical and cybernetic methods | `sequential-*`: analysis, search, games | Models, algorithms, explicit state and the assumptions under which a result holds. |
| Reusable engineering platform | `sequentialist-*`, including [core](https://github.com/andre-a-no/sequentialist-core) and [visuals](https://github.com/andre-a-no/sequentialist-visuals) | Durable application execution, storage, recovery, audit and presentation, according to each package's implemented scope. |
| Domain applications | `sequentialist-*`, including [ab](https://github.com/andre-a-no/sequentialist-ab), [quality](https://github.com/andre-a-no/sequentialist-quality), [monitor](https://github.com/andre-a-no/sequentialist-monitor), [clinical](https://github.com/andre-a-no/sequentialist-clinical) and [agentic](https://github.com/andre-a-no/sequentialist-agentic) | Subject-specific goals, workflows, adapters and user-facing decisions built from the methods and engineering components they need. |

Both the engineering platform and applications use the `sequentialist-*`
prefix. The platform is an open family of reusable packages; `core` currently
provides durable tasks built around `sequential-analysis` runs. This organization
does not imply that every combination already has an integration.

Across the ecosystem, state, information available to a decision, randomness,
costs and stopping reasons should be explicit. Evidence, resource expenditure
and real-world effects have separate meanings. Statistical validity, derivability
under supplied rules, properties of an interaction model and reliable execution
each require their own justification; a guarantee in one layer does not
automatically establish a guarantee in another.

### This package's role

**Layer: reusable engineering platform.** Visuals presents caller-supplied
search provenance and participant events as portable views. Mathematical
algorithms produce the records; applications supply their subject meaning.
Rendering does not validate a proof, calibrate a score or establish a statistical
guarantee. The current development renderer is independent of core and the
mathematical packages.

```bash
python -m pip install -e .
python -m pytest
```

## Search and AND/OR obligations

```python
from pathlib import Path
from sequentialist.visuals import render_search

graph = {
    "nodes": [
        {"id": "A", "label": "Known A", "status": "given"},
        {"id": "B", "label": "Known B", "status": "given"},
        {"id": "C", "label": "Goal C"},
    ],
    "rules": [{"id": "r1", "label": "A and B imply C",
               "premises": ["A", "B"], "conclusion": "C"}],
}
Path("search.html").write_text(render_search(graph), encoding="utf-8")
```

Each rule is an AND junction over its premises. Several rules leading to the
same conclusion are OR alternatives. Node IDs and rule IDs are unique within
their respective sets. Labels default to IDs; statuses are optional caller-owned
text. Premises and conclusions must reference supplied nodes. Empty premises
are displayed as a caller-supplied axiom, without asserting that it is true.

The diagram uses a layered layout for acyclic graphs and a circular layout for
cyclic graphs. Cycles are shown with an explicit notice; visualization is not a
proof checker. Complete labels and rule connections remain in the text records
even when the drawing abbreviates a long label.

## Participant timeline

```python
from pathlib import Path
from sequentialist.visuals import render_timeline

events = [
    {"id": "request", "time": 0, "actor": "Alice", "kind": "submitted"},
    {"id": "wait", "time": 0, "actor": "Bob", "kind": "waiting"},
    {"id": "done", "time": 3, "actor": "Alice", "kind": "completed",
     "cause": "request", "data": {"cost": 2}},
]
Path("timeline.html").write_text(render_timeline(events), encoding="utf-8")
```

Every event has a unique string `id`, finite numeric `time`, non-empty `actor`
and `kind`, optional `cause` (another supplied event ID), and optional finite JSON
`data`. The caller defines the shared model-time scale. Unknown causes, causal
cycles and causes timestamped later than their effects are rejected. For real
distributed logs, map clock/causality semantics explicitly before rendering;
this schema does not reconcile unsynchronized clocks.

Rows keep the supplied order. Equal-time events and adjacent rows do not imply
causality; only explicit cause links produce arrows. Independent participants
appear in separate lanes. The renderer never invents a global event schedule.

## Integration boundary

`render_search(graph, *, title="Search provenance")` and
`render_timeline(events, *, title="Participant events")` return strings and do
not write files or mutate their inputs. Callers adapt their own search/game/core
objects to the documented JSON-friendly schemas. The package has no dependency
on the mathematical libraries, LLM clients or a particular application.

These are bounded initial inspection views, not a live dashboard, layout engine
for very large graphs, proof validator, event scheduler or operational audit
verifier. Generated views reflect exactly the supplied subset of records.

License: AGPL-3.0-only; see LICENSE.

## Find the documentation

- [Overview and FAQ](docs/overview.md): plain-language use cases, input/output
  expectations and a workflow for people who do not program.
- [Обзор и частые вопросы на русском](docs/overview.ru.md).
- [Repository guidance](AGENTS.md): source map and proportionate check commands.
- [Curated reading index](llms.txt): a concise entry point for readers and
  assistants. Automatic discovery and web indexing depend on the client/service.
