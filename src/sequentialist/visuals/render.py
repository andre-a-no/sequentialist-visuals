# SPDX-License-Identifier: AGPL-3.0-only
"""Standalone, escaped HTML with SVG diagrams and complete textual records."""
from __future__ import annotations

import html
import json
import math
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


def _text(value: Any, field: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not value and not empty):
        raise ValueError(f"{field} must be {'a' if empty else 'a non-empty'} string")
    return value


def _object(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _array(value: Any, field: str) -> Sequence[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be an array")
    return value


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _json(value: Any) -> str:
    # Reject lossy integer-key coercion and non-finite/non-JSON payloads.
    def validate(item: Any) -> None:
        if item is None or type(item) in (str, int, bool):
            return
        if type(item) is float and math.isfinite(item):
            return
        if isinstance(item, list):
            for child in item:
                validate(child)
            return
        if isinstance(item, dict) and all(isinstance(key, str) for key in item):
            for child in item.values():
                validate(child)
            return
        raise ValueError("data must contain finite JSON values and string object keys")

    try:
        validate(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    except (TypeError, RecursionError) as exc:
        raise ValueError("data must contain finite JSON values") from exc


_CSS = """
body{font:16px/1.5 system-ui,sans-serif;color:#172634;background:#f4f6f8;margin:0}
main{max-width:1100px;margin:auto;padding:2rem}h1,h2{line-height:1.2}
.diagram{overflow:auto;background:white;border:1px solid #ccd6de;border-radius:8px;padding:1rem}
svg{display:block;min-width:600px;max-width:100%;height:auto}
svg text{font:13px system-ui,sans-serif;fill:#172634}
svg .node{fill:#edf5fc;stroke:#376b94}svg .rule{fill:#fff2d6;stroke:#977130}
svg .link{stroke:#647786;stroke-width:1.5;fill:none}svg .lane{stroke:#cbd5de}
svg .event{fill:#376b94;stroke:white;stroke-width:2}
table{border-collapse:collapse;width:100%;background:white;margin:1rem 0}
th,td{text-align:left;vertical-align:top;padding:.6rem;border:1px solid #d9e0e6}
th{background:#e7edf2}pre{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;font-size:.85rem}
.note{color:#425765}.rule-card{padding:.8rem;margin:.6rem 0;background:white;border-left:4px solid #977130}
code{overflow-wrap:anywhere}a{color:#245a83}
"""


def _page(title: str, body: str) -> str:
    title = _text(title, "title")
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_escape(title)}</title><style>{_CSS}</style></head>"
        f"<body><main><h1>{_escape(title)}</h1>{body}</main></body></html>"
    )


@dataclass(frozen=True)
class _Node:
    id: str
    label: str
    status: str


@dataclass(frozen=True)
class _Rule:
    id: str
    label: str
    premises: tuple[str, ...]
    conclusion: str


def _search_records(graph: Mapping[str, Any]) -> tuple[list[_Node], list[_Rule]]:
    graph = _object(graph, "graph")
    nodes = []
    node_ids: set[str] = set()
    for raw in _array(graph.get("nodes"), "nodes"):
        item = _object(raw, "node")
        key = _text(item.get("id"), "node.id")
        if key in node_ids:
            raise ValueError(f"duplicate node id {key!r}")
        node_ids.add(key)
        nodes.append(_Node(key, _text(item.get("label", key), "node.label", empty=True),
                           _text(item.get("status", ""), "node.status", empty=True)))
    rules = []
    rule_ids: set[str] = set()
    for raw in _array(graph.get("rules", []), "rules"):
        item = _object(raw, "rule")
        key = _text(item.get("id"), "rule.id")
        if key in rule_ids:
            raise ValueError(f"duplicate rule id {key!r}")
        rule_ids.add(key)
        premises = tuple(_text(value, "premise") for value in _array(item.get("premises"), "premises"))
        conclusion = _text(item.get("conclusion"), "conclusion")
        if len(set(premises)) != len(premises):
            raise ValueError(f"rule {key!r} contains duplicate premises")
        if any(value not in node_ids for value in (*premises, conclusion)):
            raise ValueError(f"rule {key!r} references an unknown node")
        rules.append(_Rule(key, _text(item.get("label", key), "rule.label", empty=True),
                           premises, conclusion))
    return nodes, rules


def _positions(count: int, links: list[tuple[int, int]]) -> tuple[dict[int, tuple[float, float]], bool]:
    """Layer DAGs; use a circular layout for cycles without certifying a proof."""
    adjacent: list[list[int]] = [[] for _ in range(count)]
    incoming = [0] * count
    ranks = [0] * count
    for source, target in links:
        adjacent[source].append(target)
        incoming[target] += 1
    queue = deque(index for index in range(count) if incoming[index] == 0)
    visited = 0
    while queue:
        source = queue.popleft()
        visited += 1
        for target in adjacent[source]:
            ranks[target] = max(ranks[target], ranks[source] + 1)
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    if visited != count:
        radius = max(150.0, count * 25.0)
        return {
            i: (radius + 100 + radius * math.cos(2 * math.pi * i / count),
                radius + 60 + radius * math.sin(2 * math.pi * i / count))
            for i in range(count)
        }, True
    rows: dict[int, int] = {}
    points = {}
    for index, rank in enumerate(ranks):
        row = rows.get(rank, 0)
        rows[rank] = row + 1
        points[index] = (100.0 + rank * 170, 55.0 + row * 100)
    return points, False


def _svg_open(width: float, height: float, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" '
        f'role="img" aria-label="{_escape(label)}">'
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#647786"/></marker></defs>'
    )


def render_search(graph: Mapping[str, Any], *, title: str = "Search provenance") -> str:
    """Render nodes and AND-rules; multiple rules for one conclusion are OR alternatives.

    Node schema: id, optional label/status. Rule schema: id, premises, conclusion,
    optional label. Labels/status are displayed as supplied, never interpreted.
    This function validates references, not logical or statistical correctness.
    """
    nodes, rules = _search_records(graph)
    indices = {node.id: index for index, node in enumerate(nodes)}
    links: list[tuple[int, int]] = []
    for offset, rule in enumerate(rules, len(nodes)):
        links.extend((indices[premise], offset) for premise in rule.premises)
        links.append((offset, indices[rule.conclusion]))
    positions, cyclic = _positions(len(nodes) + len(rules), links)
    width = max((point[0] for point in positions.values()), default=500) + 110
    height = max((point[1] for point in positions.values()), default=40) + 70
    svg = [_svg_open(max(600, width), height, "Search states and AND-rule connections")]
    for source, target in links:
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        length = max(1.0, math.hypot(x2 - x1, y2 - y1))
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        svg.append(f'<path class="link" d="M {x1 + dx * 32:g} {y1 + dy * 20:g} '
                   f'L {x2 - dx * 32:g} {y2 - dy * 20:g}" marker-end="url(#arrow)"/>')
    for index, node in enumerate(nodes):
        x, y = positions[index]
        label = node.label if len(node.label) <= 22 else node.label[:19] + "…"
        svg.append(f'<g><title>{_escape(node.label)}</title><rect class="node" '
                   f'x="{x - 75:g}" y="{y - 23:g}" width="150" height="46" rx="6"/>'
                   f'<text x="{x:g}" y="{y + 5:g}" text-anchor="middle">{_escape(label)}</text></g>')
    for index, rule in enumerate(rules, len(nodes)):
        x, y = positions[index]
        svg.append(f'<g><title>{_escape(rule.label)}</title><circle class="rule" '
                   f'cx="{x:g}" cy="{y:g}" r="25"/><text x="{x:g}" y="{y + 5:g}" '
                   'text-anchor="middle">AND</text></g>')
    svg.append("</svg>")
    body = (
        '<p class="note">Each AND junction requires all its premises. Different rules for the '
        'same conclusion are OR alternatives. Status labels are supplied by the caller; '
        'this view does not validate a proof or infer a guarantee.</p>'
        f'<div class="diagram">{"".join(svg)}</div>'
    )
    if cyclic:
        body += '<p class="note">Cycles are present. This drawing does not certify a valid derivation.</p>'
    body += '<h2>States</h2><table><thead><tr><th>ID</th><th>Label</th><th>Status</th></tr></thead><tbody>'
    for index, node in enumerate(nodes):
        body += (f'<tr id="node-{index}"><td>{_escape(node.id)}</td><td>{_escape(node.label)}</td>'
                 f'<td>{_escape(node.status)}</td></tr>')
    body += '</tbody></table><h2>Rules and obligations</h2>'
    for rule in rules:
        premises = " ∧ ".join(
            f'<a href="#node-{indices[key]}">{_escape(key)}</a>' for key in rule.premises
        ) or "No premises (caller-supplied axiom)"
        body += (f'<div class="rule-card"><strong>{_escape(rule.label)}</strong> '
                 f'<code>({_escape(rule.id)})</code><br>{premises} → '
                 f'<a href="#node-{indices[rule.conclusion]}">{_escape(rule.conclusion)}</a></div>')
    if not nodes:
        body += '<p>No states supplied.</p>'
    return _page(title, body)


@dataclass(frozen=True)
class _Event:
    id: str
    time: int | float
    actor: str
    kind: str
    cause: str | None
    data_json: str


def _timeline_records(events: Sequence[Mapping[str, Any]]) -> list[_Event]:
    records = []
    ids = set()
    for raw in _array(events, "events"):
        item = _object(raw, "event")
        key = _text(item.get("id"), "event.id")
        if key in ids:
            raise ValueError(f"duplicate event id {key!r}")
        ids.add(key)
        time = item.get("time")
        if isinstance(time, bool) or not isinstance(time, (int, float)):
            raise ValueError("event.time must be a finite number")
        try:
            finite = math.isfinite(time)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError("event.time must be a finite number")
        cause = item.get("cause")
        if cause is not None:
            cause = _text(cause, "event.cause")
        records.append(_Event(key, time, _text(item.get("actor"), "event.actor"),
                              _text(item.get("kind"), "event.kind"), cause, _json(item.get("data"))))
    by_id = {event.id: event for event in records}
    for event in records:
        visited = {event.id}
        source = event
        while source.cause is not None:
            if source.cause not in by_id:
                raise ValueError(f"event {source.id!r} references an unknown cause")
            if source.cause in visited:
                raise ValueError("event causes contain a cycle")
            parent = by_id[source.cause]
            if parent.time > source.time:
                raise ValueError("a cause cannot have a later time than its effect")
            visited.add(parent.id)
            source = parent
    return records


def render_timeline(events: Sequence[Mapping[str, Any]], *, title: str = "Participant events") -> str:
    """Render supplied model-time events in actor lanes and an unsorted record table.

    Events have id, finite time, actor, kind, optional cause and JSON data. Times
    use a caller-declared common scale. Only explicit cause links imply causality;
    equal-time events and input row order do not establish causal ordering.
    """
    records = _timeline_records(events)
    actors = list(dict.fromkeys(event.actor for event in records))
    low = min((event.time for event in records), default=0)
    high = max((event.time for event in records), default=0)
    scale = max(abs(float(low)), abs(float(high)), 1.0)
    origin = float(low) / scale
    spread = float(high) / scale - origin
    collisions: dict[tuple[str, int | float], int] = {}
    for event in records:
        pair = (event.actor, event.time)
        collisions[pair] = collisions.get(pair, 0) + 1
    lanes: dict[str, int] = {}
    baseline = 55
    for actor in actors:
        lanes[actor] = baseline
        slots = max(count for (name, _), count in collisions.items() if name == actor)
        baseline += max(90, slots * 14 + 45)
    positions: dict[str, tuple[float, int]] = {}
    collisions.clear()
    for event in records:
        x = 190 + ((float(event.time) / scale - origin) / spread * 650 if spread else 325)
        slot = collisions.get((event.actor, event.time), 0)
        collisions[(event.actor, event.time)] = slot + 1
        # Same-actor, equal-time events occupy separate vertical positions.
        positions[event.id] = (x, lanes[event.actor] + slot * 14)
    lane_height = max((point[1] for point in positions.values()), default=60) + 50
    svg = [_svg_open(910, lane_height, "Participant lanes with explicit causal links")]
    for actor, y in lanes.items():
        label = actor if len(actor) <= 20 else actor[:17] + "…"
        svg.append(f'<text x="8" y="{y + 5}"><title>{_escape(actor)}</title>{_escape(label)}</text>'
                   f'<path class="lane" d="M 180 {y} L 865 {y}"/>')
    for event in records:
        if event.cause is not None:
            x1, y1 = positions[event.cause]
            x2, y2 = positions[event.id]
            svg.append(f'<path class="link" d="M {x1:g} {y1:g} L {x2:g} {y2:g}" '
                       'marker-end="url(#arrow)"/>')
    for index, event in enumerate(records):
        x, y = positions[event.id]
        svg.append(f'<g><title>{_escape(event.actor)}: {_escape(event.kind)} '
                   f'@ {_escape(event.time)}</title><circle class="event" cx="{x:g}" cy="{y:g}" r="6"/>'
                   f'<text x="{x:g}" y="{y - 12:g}" text-anchor="middle">#{index + 1}</text></g>')
    svg.append("</svg>")
    body = (
        '<p class="note">Times use the caller\'s common model-time scale. Rows preserve input order. '
        'Equal-time events and adjacent rows imply no causal order; arrows show only explicit causes. '
        'This view does not infer cooperation, correctness or successful execution.</p>'
        f'<div class="diagram">{"".join(svg)}</div>'
        '<h2>Event records</h2><table><thead><tr><th># / ID</th><th>Time</th><th>Participant</th>'
        '<th>Kind</th><th>Cause</th><th>Data</th></tr></thead><tbody>'
    )
    indices = {event.id: index for index, event in enumerate(records)}
    for index, event in enumerate(records):
        cause = (f'<a href="#event-{indices[event.cause]}">{_escape(event.cause)}</a>'
                 if event.cause is not None else "—")
        body += (f'<tr id="event-{index}"><td>#{index + 1} / {_escape(event.id)}</td>'
                 f'<td>{_escape(event.time)}</td><td>{_escape(event.actor)}</td>'
                 f'<td>{_escape(event.kind)}</td><td>{cause}</td><td><pre>{_escape(event.data_json)}</pre></td></tr>')
    body += '</tbody></table>'
    if not records:
        body += '<p>No events supplied.</p>'
    return _page(title, body)
