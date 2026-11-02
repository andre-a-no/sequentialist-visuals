# SPDX-License-Identifier: AGPL-3.0-only
"""Rendering preserves records, isolation and explicit causal meaning."""
from __future__ import annotations

import copy
from html.parser import HTMLParser
from xml.etree import ElementTree

import pytest

from sequentialist.visuals import render_search, render_timeline


def graph():
    return {
        "nodes": [{"id": "a", "label": "Given A", "status": "given"},
                  {"id": "b", "label": "Given B"}, {"id": "c", "label": "Goal C"}],
        "rules": [{"id": "both", "premises": ["a", "b"], "conclusion": "c", "label": "A and B"},
                  {"id": "alternative", "premises": ["a"], "conclusion": "c"}],
    }


def events():
    # Supplied out of time order to ensure rendering does not invent a scheduler.
    return [{"id": "finished", "time": 4, "actor": "Alice", "kind": "completed", "cause": "start"},
            {"id": "start", "time": 0, "actor": "Alice", "kind": "admitted", "data": {"job": "A"}},
            {"id": "wait", "time": 0, "actor": "Bob", "kind": "waiting"}]


def svg(document):
    return ElementTree.fromstring(document[document.index("<svg "):document.index("</svg>") + 6])


def test_search_shows_conjunctive_premises_and_alternative_rules():
    source = graph()
    before = copy.deepcopy(source)
    document = render_search(source)
    assert source == before
    assert 'href="#node-0">a</a> ∧ <a href="#node-1">b</a>' in document
    assert "OR alternatives" in document
    assert "alternative" in document
    assert "given" in document
    assert len(svg(document).findall(".//{*}circle")) == 2  # distinct rule junctions
    assert "does not validate a proof" in document


def test_untrusted_text_cannot_insert_html_svg_attributes_or_script():
    attack = '<script>alert("x")</script><img src=x onerror=alert(1)>'
    source = {"nodes": [{"id": attack, "label": attack, "status": attack}],
              "rules": [{"id": attack, "label": attack, "premises": [], "conclusion": attack}]}
    document = render_search(source, title=attack)
    assert "<script>" not in document
    assert "<img " not in document
    assert "&lt;script&gt;" in document
    svg(document)

    class Tags(HTMLParser):
        def handle_starttag(self, tag, attrs):
            assert tag not in {"script", "img", "iframe"}
            assert not any(key.startswith("on") for key, value in attrs)

    Tags().feed(document)
    document = render_timeline([{"id": attack, "time": 0, "actor": attack, "kind": attack,
                                 "data": {attack: attack}}], title=attack)
    assert "<script>" not in document
    assert "&lt;script&gt;" in document
    Tags().feed(document)
    svg(document)


@pytest.mark.parametrize("change", [
    lambda d: d["nodes"].append({"id": "a"}),
    lambda d: d["rules"].append(copy.deepcopy(d["rules"][0])),
    lambda d: d["rules"][0].update(conclusion="missing"),
    lambda d: d["rules"][0].update(premises=["missing"]),
    lambda d: d["rules"][0].update(premises=["a", "a"]),
    lambda d: d["nodes"][0].update(id=1),
    lambda d: d.update(nodes=None),
])
def test_ambiguous_or_dangling_search_records_are_rejected(change):
    source = graph()
    change(source)
    with pytest.raises(ValueError):
        render_search(source)


def test_cyclic_graph_is_displayed_without_certifying_a_derivation():
    source = graph()
    source["rules"].append({"id": "cycle", "premises": ["c"], "conclusion": "a"})
    document = render_search(source)
    assert "Cycles are present" in document
    svg(document)


def test_timeline_preserves_order_and_only_explicit_causality():
    source = events()
    before = copy.deepcopy(source)
    document = render_timeline(source)
    assert source == before
    assert document.index("#1 / finished") < document.index("#2 / start") < document.index("#3 / wait")
    assert 'href="#event-1">start</a>' in document
    assert "Equal-time events and adjacent rows imply no causal order" in document
    # Three event markers, but only the caller's one causal arrow.
    diagram = svg(document)
    assert len(diagram.findall(".//{*}circle")) == 3
    assert len([path for path in diagram.findall(".//{*}path") if path.get("class") == "link"]) == 1


@pytest.mark.parametrize("change", [
    lambda e: e.append(copy.deepcopy(e[0])),
    lambda e: e[0].update(cause="missing"),
    lambda e: e[0].update(cause="finished"),
    lambda e: e[1].update(cause="finished"),
    lambda e: e[0].update(time=float("nan")),
    lambda e: e[0].update(time=True),
    lambda e: e[0].update(data={1: "not a JSON object key"}),
    lambda e: e[0].update(data=float("inf")),
])
def test_malformed_timeline_records_are_rejected(change):
    source = events()
    change(source)
    with pytest.raises(ValueError):
        render_timeline(source)


def test_same_time_causal_cycle_is_rejected():
    with pytest.raises(ValueError, match="cycle"):
        render_timeline([{"id": "a", "time": 0, "actor": "A", "kind": "x", "cause": "b"},
                         {"id": "b", "time": 0, "actor": "B", "kind": "x", "cause": "a"}])


def test_empty_views_and_unicode_are_portable_and_deterministic():
    assert "No states supplied" in render_search({"nodes": []})
    assert "No events supplied" in render_timeline([])
    document = render_search({"nodes": [{"id": "α", "label": "Дано → цель"}]})
    assert "Дано → цель" in document
    assert "<script" not in document
    assert 'src="http' not in document and 'href="http' not in document
    assert document == render_search({"nodes": [{"id": "α", "label": "Дано → цель"}]})


def test_extreme_finite_timestamps_do_not_overflow_svg_coordinates():
    document = render_timeline([
        {"id": "a", "time": -1e308, "actor": "A", "kind": "x"},
        {"id": "b", "time": 1e308, "actor": "B", "kind": "x", "cause": "a"},
    ])
    for element in svg(document).iter():
        for value in element.attrib.values():
            assert "nan" not in value.lower() and "inf" not in value.lower()


def test_many_equal_time_events_remain_in_their_participant_lane():
    source = [{"id": str(index), "time": 0, "actor": "A", "kind": "x"} for index in range(12)]
    source.append({"id": "other", "time": 0, "actor": "B", "kind": "x"})
    circles = svg(render_timeline(source)).findall(".//{*}circle")
    assert max(float(item.attrib["cy"]) for item in circles[:-1]) < float(circles[-1].attrib["cy"])
