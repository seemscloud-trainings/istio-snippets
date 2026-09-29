#!/usr/bin/env python3
"""Render ProxyConfig CRD and Pod-annotation examples without running workloads."""

import argparse
from pathlib import Path

from PIL import Image
import yaml

from render_service_entry import Canvas, BLUE, GREEN, MUTED, BORDER
from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = (
    ("concurrency", "Concurrency · ProxyConfig"),
    ("distroless", "Distroless · ProxyConfig"),
    ("dns-capture", "DNS capture · ProxyConfig"),
    ("startup", "Startup · Pod annotation"),
    ("shutdown", "Shutdown · Pod annotation"),
    ("stats", "Metrics · Pod annotation"),
)


def row(left, middle, right, *, problem=False, stopped=False,
        titles=("Container", "istio-proxy", "Result"), arrows=("", "")):
    return dict(left=left, middle=middle, right=right, problem=problem,
                stopped=stopped, titles=titles, arrows=arrows)


def content(slug, documents):
    obj = documents[0]
    if obj["kind"] == "ProxyConfig":
        spec = obj["spec"]
        title = "ProxyConfig"
    else:
        spec = yaml.safe_load(obj["metadata"]["annotations"]["proxy.istio.io/config"])
        title = "proxy.istio.io/config"
    settings = [] if obj["kind"] == "ProxyConfig" else [f"Pod: {obj['metadata']['name']}"]
    extra = None
    if slug == "concurrency":
        workers = spec["concurrency"]
        settings.append(f"concurrency: {workers}")
        rows = [
            row(["curl http://wp.pl", "Load within CPU budget"],
                [f"{workers} worker threads", "CPU available"], ["Requests complete"], arrows=("HTTP", "")),
            row(["curl http://wp.pl", "Load exceeds CPU budget"],
                [f"{workers} worker threads", "CPU saturated"], ["Queue / latency increases", "No fixed HTTP error code"],
                problem=True, arrows=("HTTP", "")),
        ]
    elif slug == "distroless":
        settings.append("image.imageType: " + spec["image"]["imageType"])
        rows = [
            row(["curl http://wp.pl"], ["Distroless Envoy", "HTTP routing works"], ["HTTP response"], arrows=("HTTP", "")),
            row(["kubectl exec app \\", "-c istio-proxy -- sh"],
                ["Distroless image", "No sh executable"], ["exec fails", "HTTP routing still works"],
                problem=True, titles=("Terminal", "istio-proxy", "Result")),
        ]
    elif slug == "dns-capture":
        settings.append("ISTIO_META_DNS_CAPTURE: " + spec["environmentVariables"]["ISTIO_META_DNS_CAPTURE"])
        service = documents[1]["spec"]
        vip = service["addresses"][0]
        host = service["hosts"][0]
        extra = ("ServiceEntry", [f"hosts: [{host}]", f"addresses: [{vip}]",
                                  "resolution: " + service["resolution"], "exportTo: [.]" ])
        rows = [
            row([f"curl http://{host}", f"DNS → {vip}"],
                [f"DNS → {vip}", "Envoy DNS → 198.51.100.20"],
                ["198.51.100.20:80", "HTTP response"], arrows=("HTTP", "HTTP")),
            row([f"curl http://{host}", f"DNS → {vip}"],
                ["Initial upstream DNS lookup fails", "No endpoints → HTTP 503"],
                ["wp.pl not reached"], problem=True, stopped=True, arrows=("HTTP", "")),
        ]
    elif slug == "startup":
        settings.append("holdApplicationUntilProxyStarts: " + str(spec["holdApplicationUntilProxyStarts"]).lower())
        rows = [
            row(["Pod created"], ["Proxy becomes ready"],
                ["Application starts", "curl http://wp.pl"], titles=("Startup", "istio-proxy", "Container")),
            row(["Pod created"], ["Proxy never becomes ready"],
                ["Application waits", "No HTTP request sent"], problem=True, stopped=True,
                titles=("Startup", "istio-proxy", "Container")),
        ]
    elif slug == "shutdown":
        drain = spec["terminationDrainDuration"]
        grace = obj["spec"]["terminationGracePeriodSeconds"]
        settings.extend([f"terminationDrainDuration: {drain}", f"terminationGracePeriodSeconds: {grace}"])
        rows = [
            row(["curl http://app.shop", "Request in flight at termination"],
                [f"Drain budget: {drain}", "Request finishes after 20 s"], ["Response completed", "20 s < 30 s"],
                titles=("Client", "Proxy shutdown", "Client result")),
            row(["curl http://app.shop", "Request needs another 40 s"],
                [f"Drain budget exhausted: {drain}", "Remaining connection closed"], ["Request interrupted", "40 s > 30 s"],
                problem=True, titles=("Client", "Proxy shutdown", "Client result")),
        ]
    else:
        regexes = spec["proxyStatsMatcher"]["inclusionRegexps"]
        settings.extend(["proxyStatsMatcher.inclusionRegexps:", *regexes])
        rows = [
            row(["curl http://wp.pl", "First request succeeds"],
                ["No retries / no pool overflow"], ["upstream_rq_retry: +0", "pending_overflow: +0"],
                titles=("Container", "Envoy counters", "Prometheus"), arrows=("HTTP", "metrics")),
            row(["curl http://wp.pl", "Backend returns 503"],
                ["Existing VirtualService retries ×2", "Counters record those retries"],
                ["upstream_rq_retry: +2", "Retry behavior is unchanged"], problem=True,
                titles=("Container", "Envoy counters", "Prometheus"), arrows=("HTTP", "metrics")),
        ]
    return title, settings, extra, rows


def render(slug, documents):
    title, settings, extra, rows = content(slug, documents)
    config_height = max(185, 85 + 31 * max(len(settings), len(extra[1]) if extra else 0))
    top = config_height + 95
    c = Canvas((1800, top + 240 * len(rows) + 10))
    if extra:
        c.card(60, 25, 800, config_height, title, settings, "neutral")
        c.card(940, 25, 800, config_height, extra[0], extra[1], "neutral")
    else:
        c.card(450, 25, 900, config_height, title, settings, "neutral")
    for index, item in enumerate(rows):
        y = top + index * 240
        if slug == "startup":
            frame_x, frame_width = 695, 1070
        elif slug == "shutdown" or (slug == "distroless" and index == 1):
            frame_x, frame_width = 695, 550
        else:
            frame_x, frame_width = 35, 1210
        c.box(frame_x, y - 38, frame_width, 233, "white", BORDER)
        c.text(frame_x + 20, y - 27, "Pod app", 21, MUTED, True)
        for edge in (frame_x, frame_x + frame_width):
            if 590 < edge < 720 or 1220 < edge < 1360:
                c.line([(edge, y + 74), (edge, y + 102)], "white", width=6)
        c.card(60, y, 530, 175, item["titles"][0], item["left"], "app")
        c.card(720, y, 500, 175, item["titles"][1], item["middle"], "blocked" if item["problem"] else "proxy")
        c.card(1360, y, 380, 175, item["titles"][2], item["right"],
               "neutral" if item["stopped"] else "blocked" if item["problem"] else "target")
        mid = y + 88
        c.arrow([(590, mid), (720, mid)], BLUE)
        c.text(610, mid - 33, item["arrows"][0], 21, BLUE)
        if item["stopped"]:
            c.line([(1220, mid), (1290, mid)], "#a34740")
            c.line([(1282, mid - 8), (1298, mid + 8)], "#a34740")
            c.line([(1282, mid + 8), (1298, mid - 8)], "#a34740")
        else:
            c.arrow([(1220, mid), (1360, mid)], "#a34740" if item["problem"] else GREEN)
            c.text(1263, mid - 33, item["arrows"][1], 21, MUTED)
    return c.image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    parts = []
    for slug, title in EXAMPLES:
        source = ROOT / "proxy-config" / f"{slug}.yaml"
        documents = list(yaml.safe_load_all(source.read_text()))
        image = render(slug, documents)
        output = ROOT / "images/proxy-config" / f"{slug}.png"
        if args.check:
            with Image.open(output) as old:
                if old.size != image.size or old.convert("RGB").tobytes() != image.tobytes():
                    raise ValueError(f"Stale PNG: {output}")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, "PNG", optimize=True)
        parts.extend([f"#### {title}", "```yaml\n" + dump_documents(documents).rstrip() + "\n```",
                      f"![{title}]({output.relative_to(ROOT).as_posix()})"])
    output = ROOT / "PROXY-CONFIG.md"
    text = "\n\n".join(parts) + "\n"
    if args.check:
        if output.read_text() != text:
            raise ValueError("Stale ProxyConfig page")
        print("Six ProxyConfig diagrams and Markdown match their sources.")
    else:
        output.write_text(text)
        print(output.name)


if __name__ == "__main__":
    main()
