#!/usr/bin/env python3
"""Render the Forgejo Trouble routes as comment-free snippets and request flows."""
import argparse
import copy
from pathlib import Path

from PIL import Image
import yaml

from render_service_entry import Canvas, BLUE, GREEN, MUTED, BORDER
from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "virtual-service"
HOST = yaml.safe_load((MANIFESTS / "trouble.yaml").read_text())["spec"]["hosts"][0]


def case(path, envoy, backend, *, reaches=True, header=False, inbound=False,
         problem=False, backend_problem=False):
    first, rest = HOST.split(".", 1)
    command = (["curl -H 'x-demo-fault: yes' \\", f"http://{first}.\\"] if header
               else [f"curl http://{first}.\\"])
    command.extend([rest + "\\", f"/test/cosmos-{path}"])
    return dict(command=command, envoy=envoy, backend=backend, reaches=reaches, inbound=inbound,
                problem=problem or not reaches, backend_problem=backend_problem)


GROUPS = [
    ("no-retry", "No retry", ["trouble-healthy", "trouble-flaky"], [
        case("healthy", ["No retry", "Client ← 200"], ["200 · 0 ms"]),
        case("flaky", ["No retry", "Client ← 200"], ["50%: 200 · 0 ms"]),
        case("flaky", ["No retry", "Client ← 503"], ["50%: 503 · 0 ms"], problem=True, backend_problem=True),
    ]),
    ("retry", "Retry", ["trouble-retry"], [
        case("retry", ["First attempt succeeds", "Client ← 200"], ["Attempt 1: 200"]),
        case("retry", ["503 → retry → 200", "Client ← 200"], ["Attempt 1: 503", "Attempt 2: 200"], backend_problem=True),
        case("retry", ["503 → retry → retry", "Client ← 503"], ["All 3 attempts: 503"], problem=True, backend_problem=True),
    ]),
    ("retry-timeout", "Per-try timeout", ["trouble-retry-timeout"], [
        case("retry-timeout", ["100 ms < 500 ms per try", "Client ← 200 · no retry"], ["200 after 100 ms"]),
        case("retry-timeout", ["500 ms per try · max 3 tries", "Client ← 504 · budget 3 s"], ["Response takes 2 s", "Each try times out"], problem=True, backend_problem=True),
    ]),
    ("fault-abort", "Fault abort", ["trouble-fault-abort"], [
        case("fault-abort", ["50%: forward", "Client ← 200"], ["200 · 0 ms"]),
        case("fault-abort", ["50%: abort here", "Client ← 503"], ["Not reached"], reaches=False),
    ]),
    ("fault-delay", "Fault delay", ["trouble-healthy", "trouble-fault-delay"], [
        case("healthy", ["No injected delay", "Client ← 200"], ["200 · 0 ms"]),
        case("fault-delay", ["Injected delay: 2 s", "Client ← 200 after delay"], ["200 · 0 ms"], problem=True),
    ]),
    ("header-fault", "Header match", ["trouble-header-fault", "trouble-header-fault-healthy"], [
        case("header-fault", ["Fallback route → forward", "Client ← 200"], ["200 · 0 ms"]),
        case("header-fault", ["x-demo-fault: yes", "Client ← 503 · abort here"], ["Not reached"], reaches=False, header=True),
    ]),
    ("connections", "Connection pool", ["trouble-connections"], [
        case("connections", ["1 active + 1 pending", "Client ← 200"], ["200 after 3 s"]),
        case("connections", ["Pool full → reject overflow", "Client ← 503"], ["Not reached"], reaches=False),
    ]),
    ("timeout", "Request timeout", ["trouble-timeout"], [
        case("timeout", ["100 ms < timeout 1 s", "Client ← 200 after 100 ms"], ["200 after 100 ms"]),
        case("timeout", ["1 s elapsed → stop waiting", "Client ← 504 after 1 s"], ["Response takes 3 s", "3 s > timeout 1 s"], problem=True, backend_problem=True),
    ]),
    ("outlier", "Outlier detection", ["trouble-no-retry"], [
        case("outlier", ["Pod A healthy → route normally", "Client ← 200"], ["Pod A: 200"]),
        case("outlier", ["3 consecutive 5xx from Pod A", "Pod A ejected · base 5 s"], ["Pod A: 503, 503, 503"], problem=True, backend_problem=True),
        case("outlier", ["Pod A ejected · base 5 s", "Client ← 200 from Pod B"], ["Pod B: 200"]),
    ]),
    ("rate-limit", "Local rate limit", ["trouble-rate-limit"], [
        case("rate-limit", ["Forward to Trouble", "Client ← 200"], ["Same inbound Envoy", "3 tokens / 10 s → API 200"], inbound=True),
        case("rate-limit", ["Forward to Trouble", "Client ← 429"], ["Bucket empty → 429", "API not reached"], inbound=True, problem=True, backend_problem=True),
    ]),
]


def render(slug, settings, cases):
    height = max(160, 85 + 31 * len(settings))
    top = height + 85
    c = Canvas((1800, top + len(cases) * 270 + 10))
    c.card(415, 25, 970, height, "Routing", settings, "neutral")
    for i, item in enumerate(cases):
        y = top + i * 270
        c.box(35, y, 1210, 250, "white", BORDER)
        c.text(60, y + 12, "Client Pod", 23, MUTED, True)
        c.text(1350, y + 12, "Trouble Pods", 23, MUTED, True)
        c.card(60, y + 48, 610, 185, "Container", item["command"], "app")
        c.card(780, y + 48, 430, 185, "Envoy", item["envoy"], "blocked" if item["problem"] else "proxy")
        c.card(1350, y + 48, 400, 185, "Inbound Envoy" if item["inbound"] else "Envoy → API",
               item["backend"], "neutral" if not item["reaches"] else "blocked" if item["backend_problem"] else "target")
        mid = y + 145
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
        text = dump_documents(objects).rstrip()
        parts.extend([f"#### {title}", "```yaml\n" + text + "\n```",
                      f"![{title}](images/virtual-service/{slug}.png)"])
        write_image(slug, render(slug, settings, cases), args.check)

    section("host", "Subsets", [dr],
            [f"host: {HOST}", "DestinationRule subsets: scenarios / connections", "No subset → default outlier policy"],
            [case("healthy", ["Trouble Service", "Subset: scenarios"], ["Backend: playground-trouble", "Port: 80"] )])
    for slug, title, names, cases in GROUPS:
        snippet = copy.deepcopy(vs)
        snippet["metadata"]["name"] = "trouble-" + slug
        snippet["spec"]["http"] = [routes[name] for name in names]
        settings = [f"host: {HOST}"]
        first = next((routes[name] for name in names if "fault" in routes[name]), routes[names[0]])
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
