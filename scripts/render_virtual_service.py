#!/usr/bin/env python3
"""Render the Forgejo Trouble routes as comment-free snippets and request flows."""
import argparse
import copy
from pathlib import Path

from PIL import Image
import yaml

from render_service_entry import Canvas, BLUE, GREEN, MUTED, BORDER

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "virtual-service"


def case(path, envoy, backend, *, reaches=True, header=False, inbound=False):
    command = (["curl -H 'x-demo-fault: yes' \\", f"http://wp.pl/test/cosmos-{path}"] if header
               else [f"curl http://wp.pl/test/cosmos-{path}"])
    return dict(command=command, envoy=envoy, backend=backend, reaches=reaches, inbound=inbound)


GROUPS = [
    ("no-retry", "No retry", ["trouble-healthy", "trouble-flaky"], [
        case("healthy", ["No retry", "Client ← 200"], ["200 · 0 ms"]),
        case("flaky", ["No retry", "Client ← 200"], ["50%: 200 · 0 ms"]),
        case("flaky", ["No retry", "Client ← 503"], ["50%: 503 · 0 ms"]),
    ]),
    ("retry", "Retry", ["trouble-retry"], [
        case("retry", ["503 → retry → 200", "Client ← 200"], ["Attempt 1: 503", "Attempt 2: 200"]),
        case("retry", ["503 → retry → retry", "Client ← 503"], ["All 3 attempts: 503"]),
    ]),
    ("retry-timeout", "Per-try timeout", ["trouble-retry-timeout"], [
        case("retry-timeout", ["500 ms per try · max 3 tries", "Client ← 504 · budget 3 s"], ["Response takes 2 s", "Each try times out"]),
    ]),
    ("fault-abort", "Fault abort", ["trouble-fault-abort"], [
        case("fault-abort", ["50%: abort here", "Client ← 503"], ["Not reached"], reaches=False),
        case("fault-abort", ["50%: forward", "Client ← 200"], ["200 · 0 ms"]),
    ]),
    ("fault-delay", "Fault delay", ["trouble-fault-delay"], [
        case("fault-delay", ["Wait 2 s → forward", "Client ← 200"], ["200 · 0 ms"]),
    ]),
    ("header-fault", "Header match", ["trouble-header-fault", "trouble-header-fault-healthy"], [
        case("header-fault", ["x-demo-fault: yes", "Client ← 503 · abort here"], ["Not reached"], reaches=False, header=True),
        case("header-fault", ["Fallback route → forward", "Client ← 200"], ["200 · 0 ms"]),
    ]),
    ("connections", "Connection pool", ["trouble-connections"], [
        case("connections", ["1 active + 1 pending", "Client ← 200"], ["200 after 3 s"]),
        case("connections", ["Pool full → reject overflow", "Client ← 503"], ["Not reached"], reaches=False),
    ]),
    ("timeout", "Request timeout", ["trouble-timeout"], [
        case("timeout", ["Timeout: 1 s · no retries", "Client ← 504"], ["Response takes 3 s", "Client stops waiting at 1 s"]),
    ]),
    ("outlier", "Outlier detection", ["trouble-no-retry"], [
        case("outlier", ["3 consecutive 5xx from Pod A", "consecutive5xxErrors: 3"], ["Pod A: 503, 503, 503"]),
        case("outlier", ["Pod A ejected · base 5 s", "Client ← 200 from Pod B"], ["Pod B: 200"]),
    ]),
    ("rate-limit", "Local rate limit", ["trouble-rate-limit"], [
        case("rate-limit", ["Forward to Trouble", "Client ← 200"], ["Same inbound Envoy", "3 tokens / 10 s → API 200"], inbound=True),
        case("rate-limit", ["Forward to Trouble", "Client ← 429"], ["Bucket empty → 429", "API not reached"], inbound=True),
    ]),
]


def render(slug, settings, cases, show_dns=False):
    height = max(160, 85 + 31 * len(settings))
    top = height + 85
    c = Canvas((1800, top + len(cases) * 230 + 10))
    if show_dns:
        c.card(60, 25, 610, 130, "DNS", ["wp.pl → 198.51.100.10"], "dns")
    c.card(780 if show_dns else 415, 25, 970, height, "Routing", settings, "neutral")
    for i, item in enumerate(cases):
        y = top + i * 230
        c.box(35, y, 1210, 210, "white", BORDER)
        c.text(60, y + 12, "Client Pod", 23, MUTED, True)
        c.text(1350, y + 12, "Trouble Pods", 23, MUTED, True)
        c.card(60, y + 48, 610, 145, "Container", item["command"], "app")
        c.card(780, y + 48, 430, 145, "Envoy", item["envoy"], "proxy" if item["reaches"] else "blocked")
        c.card(1350, y + 48, 400, 145, "Inbound Envoy" if item["inbound"] else "Envoy → API",
               item["backend"], "target" if item["reaches"] else "neutral")
        mid = y + 125
        c.line([(1245, mid - 14), (1245, mid + 14)], "white", width=6)
        c.arrow([(670, mid), (780, mid)], BLUE)
        c.text(690, mid - 33, "HTTP", 21, BLUE)
        if item["reaches"]:
            c.arrow([(1210, mid), (1350, mid)], GREEN)
            c.text(1260, mid - 33, "HTTP", 21, GREEN)
        else:
            c.line([(1210, mid), (1285, mid)], "#a34740")
            c.line([(1277, mid - 8), (1293, mid + 8)], "#a34740")
            c.line([(1277, mid + 8), (1293, mid - 8)], "#a34740")
    return c.image


def read(name):
    return yaml.safe_load((MANIFESTS / name).read_text())


def write_image(name, image, check):
    path = ROOT / "images/virtual-service" / f"{name}.png"
    if check:
        with Image.open(path) as old:
            if old.size != image.size or old.convert("RGB").tobytes() != image.tobytes():
                raise ValueError(f"Stale image: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    vs, dr, ef = read("trouble.yaml"), read("trouble-destinationrule.yaml"), read("trouble-rate-limit.yaml")
    routes = {r["name"]: r for r in vs["spec"]["http"]}
    parts = []

    def section(slug, title, objects, settings, cases):
        text = yaml.safe_dump_all(objects, sort_keys=False).rstrip()
        parts.extend([f"#### {title}", "```yaml\n" + text + "\n```",
                      f"![{title}](images/virtual-service/{slug}.png)"])
        write_image(slug, render(slug, settings, cases, any(obj["kind"] == "ServiceEntry" for obj in objects)), args.check)

    section("host", "Host + subsets", [read("wp.yaml"), dr],
            ["ServiceEntry: wp.pl", "VirtualService routes to playground-trouble", "DestinationRule subsets: scenarios / connections", "No subset → default outlier policy"],
            [case("healthy", ["Host: wp.pl → Trouble Service", "Subset: scenarios"], ["Backend: playground-trouble", "Port: 80"] )])
    for slug, title, names, cases in GROUPS:
        snippet = copy.deepcopy(vs)
        snippet["metadata"]["name"] = "trouble-" + slug
        snippet["spec"]["http"] = [routes[name] for name in names]
        settings = ["VirtualService: wp.pl → playground-trouble:80"]
        first = routes[names[0]]
        if "fault" in first:
            fault = first["fault"]
            if "abort" in fault:
                settings.append(f"fault.abort: {fault['abort']['percentage']['value']}% → {fault['abort']['httpStatus']}")
            if "delay" in fault:
                settings.append(f"fault.delay: {fault['delay']['percentage']['value']}% → {fault['delay']['fixedDelay']}")
        elif "retries" in first:
            retries = first["retries"]
            settings.append("retries.attempts: " + str(retries["attempts"]))
            if retries.get("perTryTimeout"):
                settings.append("perTryTimeout: " + retries["perTryTimeout"])
        if "fault" not in first:
            settings.append("timeout: " + first["timeout"])
        if slug == "header-fault":
            settings.append("Order: header match → fallback")
        elif slug == "connections":
            settings.append("DestinationRule: 1 connection · 1 active · 1 pending")
        elif slug == "outlier":
            settings.append("DestinationRule: 3 × 5xx · ejection 5 s · max 50%")
        elif slug == "rate-limit":
            settings.append("EnvoyFilter: 3 tokens / 10 s per inbound Envoy")
        section(slug, title, [snippet, ef] if slug == "rate-limit" else [snippet], settings, cases)
    path = ROOT / "README.virtual-service.md"
    text = "\n\n".join(parts) + "\n"
    if args.check:
        if path.read_text() != text:
            raise ValueError("Stale VirtualService page")
        print("VirtualService page and eleven diagrams match their sources.")
    else:
        path.write_text(text)
        print(path.name)


if __name__ == "__main__":
    main()
