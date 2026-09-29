#!/usr/bin/env python3
"""Render ServiceEntry documentation and PNGs offline from the tracked manifests."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
SIZE = (1640, 580)
# Illustrative DNS answers from RFC 5737; never query live endpoints when rendering.
DNS_ANSWERS = {"wp.pl": "198.51.100.10", "backend.wp.pl": "198.51.100.20"}
INK, MUTED, BORDER = "#243347", "#65758b", "#c7d2de"
BLUE, AMBER, GREEN = "#2563a8", "#aa731d", "#267d70"
STYLES = {
    "app": ("#f5f0fa", "#b9a7ca", "#795f96"),
    "proxy": ("#edf3fc", "#a5bad8", BLUE),
    "dns": ("#fcf7ec", "#d8c18f", AMBER),
    "target": ("#edf7f4", "#a5c7bd", GREEN),
    "neutral": ("#f7f9fb", BORDER, MUTED),
}


@dataclass(frozen=True)
class Example:
    slug: str
    title: str


EXAMPLES = (
    Example("normal", "Normal"),
    Example("static-endpoint", "Override Egress IP, not DNS IP"),
    Example("original-destination", "Service Translation — original destination"),
    Example("dns-endpoint", "DNS Resolution + Different Domain"),
    Example("tls-origination", "Istio 80, egress 4433"),
)


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    path = next((path for path in candidates if Path(path).is_file()), None)
    if path is None:
        raise RuntimeError("Arial or DejaVu Sans is required; no fonts are downloaded.")
    return ImageFont.truetype(path, size * SCALE)


class Canvas:
    def __init__(self) -> None:
        self.image = Image.new("RGB", tuple(v * SCALE for v in SIZE), "white")
        self.draw = ImageDraw.Draw(self.image)

    def text(self, x, y, value, size=23, color=INK, bold=False):
        bounds = self.draw.textbbox((x * SCALE, y * SCALE), value,
                                    font=font(size, bold), anchor="lt")
        if bounds[2] > SIZE[0] * SCALE or bounds[3] > SIZE[1] * SCALE:
            raise ValueError(f"Text exceeds image bounds: {value}")
        self.draw.text((x * SCALE, y * SCALE), value,
                       font=font(size, bold), fill=color, anchor="lt")

    def box(self, x, y, w, h, fill, outline, radius=12):
        self.draw.rounded_rectangle(
            tuple(v * SCALE for v in (x, y, x + w, y + h)),
            radius=radius * SCALE, fill=fill, outline=outline, width=2 * SCALE,
        )

    def line(self, points, color=BORDER, dashed=False, width=3):
        for a, b in zip(points, points[1:]):
            length = math.dist(a, b)
            if not length:
                continue
            for start in range(0, math.ceil(length), 18 if dashed else math.ceil(length)):
                end = min(length, start + (10 if dashed else length))
                p = tuple((a[i] + (b[i] - a[i]) * start / length) * SCALE for i in (0, 1))
                q = tuple((a[i] + (b[i] - a[i]) * end / length) * SCALE for i in (0, 1))
                self.draw.line((p, q), fill=color, width=width * SCALE)

    def arrow(self, points, color=BLUE, dashed=False):
        self.line(points, color, dashed)
        a, b = points[-2:]
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        back = (b[0] - 14 * math.cos(angle), b[1] - 14 * math.sin(angle))
        wings = ((back[0] + 7 * math.sin(angle), back[1] - 7 * math.cos(angle)),
                 (back[0] - 7 * math.sin(angle), back[1] + 7 * math.cos(angle)))
        self.draw.polygon([(x * SCALE, y * SCALE) for x, y in (b, *wings)], fill=color)

    def card(self, x, y, w, h, title, lines, role):
        fill, border, accent = STYLES[role]
        self.box(x, y, w, h, fill, border)
        self.line([(x + 20, y + 19), (x + 20, y + 40)], accent, width=4)
        self.text(x + 35, y + 19, title, 23, bold=True)
        for index, line in enumerate(lines):
            if self.draw.textlength(line, font=font(21)) > (w - 40) * SCALE:
                raise ValueError(f"Card text exceeds width: {line}")
            self.text(x + 20, y + 58 + index * 31, line, 21, MUTED)


def render(example: Example, resources: list[dict]) -> Image.Image:
    entry = resources[0]["spec"]
    host = entry["hosts"][0]
    port = entry["ports"][0]
    mode = entry["resolution"]
    origination = any(resource["kind"] == "DestinationRule" for resource in resources)
    original = mode == "NONE"
    endpoint = entry.get("endpoints", [{}])[0].get("address", host)
    app_ip = DNS_ANSWERS[host]
    proxy_ip = (app_ip if original else endpoint if mode == "STATIC"
                else DNS_ANSWERS[endpoint])
    upstream_port = port.get("targetPort", port["number"])
    c = Canvas()

    c.card(70, 35, 390, 95, "DNS",
           [f"{host}  →  {app_ip}"], "dns")
    settings = [f"hosts: {host}", f"resolution: {mode}"]
    if original:
        settings.append("addresses: " + ", ".join(entry["addresses"]))
    elif "endpoints" in entry:
        settings.append(f"endpoints: {endpoint}")
    if origination:
        settings.extend([f"port: {port['number']} → targetPort: {upstream_port}",
                         "DestinationRule: tls.mode = SIMPLE"])
    c.card(650, 25, 470, 225, "ServiceEntry", settings, "neutral")

    c.box(40, 320, 1040, 235, "white", BORDER)
    for x in (265, 845):
        c.line([(x - 14, 320), (x + 14, 320)], "white", width=6)
    c.line([(1080, 436), (1080, 464)], "white", width=6)
    c.text(65, 337, "Pod", 23, MUTED, True)
    c.text(1240, 337, "External", 23, MUTED, True)
    c.arrow([(265, 375), (265, 130)], AMBER, True)
    c.arrow([(845, 250), (845, 375)], MUTED, True)

    c.card(70, 375, 390, 145, "Container",
           [f"curl {'http' if origination else 'https'}://{host}",
            f"{host}  →  {app_ip}"], "app")
    proxy_lines = [f"{host}  →  {proxy_ip}"]
    if original:
        proxy_lines.append("No IP match → ALLOW_ANY")
    elif origination:
        proxy_lines.append("HTTP :80 → HTTPS :4433")
    elif mode == "DNS":
        proxy_lines.append(f"DNS: {endpoint}")
    c.card(650, 375, 390, 145, "Envoy", proxy_lines, "proxy")
    c.card(1240, 375, 350, 145, "Destination",
           [f"{proxy_ip}:{upstream_port}", f"HTTPS host: {host}"], "target")
    c.arrow([(460, 450), (650, 450)])
    c.text(477, 412, f"{'HTTP' if origination else 'HTTPS'} :{port['number']}", 22, BLUE)
    c.arrow([(1040, 450), (1240, 450)], GREEN)
    c.text(1058, 412, f"HTTPS :{upstream_port}", 22, GREEN)
    return c.image


def documentation() -> str:
    parts = []
    for example in EXAMPLES:
        relative = f"service-entry/{example.slug}.yaml"
        parts.extend([
            f"#### {example.title}",
            "```yaml\n" + (ROOT / relative).read_text().rstrip() + "\n```",
            f"![{example.title}](images/service-entry/{example.slug}.png)",
        ])
    return "\n\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare existing outputs without writing")
    args = parser.parse_args()
    stale = []
    for example in EXAMPLES:
        manifest = ROOT / "service-entry" / f"{example.slug}.yaml"
        resources = list(yaml.safe_load_all(manifest.read_text()))
        image = render(example, resources)
        output = ROOT / "images" / "service-entry" / f"{example.slug}.png"
        if args.check:
            if not output.is_file():
                stale.append(str(output.relative_to(ROOT)))
            else:
                with Image.open(output) as previous:
                    if previous.size != image.size or previous.convert("RGB").tobytes() != image.tobytes():
                        stale.append(str(output.relative_to(ROOT)))
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, "PNG", optimize=True)
            print(output.relative_to(ROOT))
    page = ROOT / "README.service-entry.md"
    content = documentation()
    if args.check:
        if not page.is_file() or page.read_text() != content:
            stale.append(page.name)
        if stale:
            raise SystemExit("Stale generated outputs: " + ", ".join(stale))
        print("All five PNGs and the topic page match their sources.")
    else:
        page.write_text(content)
        print(page.name)


if __name__ == "__main__":
    main()
