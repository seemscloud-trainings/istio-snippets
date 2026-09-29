#!/usr/bin/env python3
"""Render compact, offline Sidecar and security examples beside their YAML."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
import yaml

from render_service_entry import Canvas, BLUE, GREEN, MUTED, BORDER

ROOT = Path(__file__).resolve().parents[1]
RED = "#a34740"


@dataclass(frozen=True)
class Case:
    source: str
    command: tuple[str, ...]
    decision: tuple[str, ...]
    allowed: bool
    transport: str = "mTLS"
    target: str = "shop/api"
    result: tuple[str, ...] = ("200 from application",)


@dataclass(frozen=True)
class Example:
    topic: str
    slug: str
    title: str
    cases: tuple[Case, ...]


def outgoing(namespace, imported=True, passthrough=False):
    service_ip = {"shop": "10.96.10.10", "payments": "10.96.20.10", "reporting": "10.96.30.10"}[namespace]
    known = (f"api.{namespace}: imported", "Route to service endpoints")
    unknown = (f"api.{namespace}: not imported",
               f"ALLOW_ANY → {service_ip}" if passthrough else "REGISTRY_ONLY → 503")
    return Case("shop/client · app=client",
                (f"curl http://api.{namespace}/orders", f"DNS → {service_ip}"),
                known if imported else unknown, imported or passthrough,
                "HTTP" if passthrough else "mTLS", f"{namespace}/api")


def peer(account, path="orders", method="GET", *, decision, allowed, plaintext=False):
    command = f"curl {'-X POST ' if method == 'POST' else ''}http://api.shop/{path}"
    return Case(f"shop/{account}{'-plain' if plaintext else ''} · SA={account}",
                (command, "No Envoy: plaintext" if plaintext else "Envoy: automatic mTLS"),
                decision, allowed, "HTTP" if plaintext else "mTLS",
                result=(f"200 · {method} /{path}",))


def jwt(token, decision, allowed, path="orders", claim=""):
    command = [f"curl http://api.shop/{path}" + (" \\" if token else "")]
    if token:
        command.append(f'-H "Authorization: Bearer ${token}"')
    if claim:
        command.append(claim)
    return Case("shop/client · Envoy injected", tuple(command), decision, allowed,
                result=(f"200 · GET /{path}",))


EXAMPLES = (
    Example("sidecar", "local-only", "Import only the local namespace", (
        outgoing("shop"), outgoing("payments", False),
    )),
    Example("sidecar", "import-service", "Import one service from another namespace", (
        outgoing("shop"), outgoing("payments"), outgoing("reporting", False),
    )),
    Example("sidecar", "allow-any", "ALLOW_ANY: an unimported service can still be reached", (
        outgoing("shop"), outgoing("payments", False, True),
    )),
    Example("peer-authorization", "strict-reader", "STRICT mTLS + allow one ServiceAccount", (
        peer("reader", decision=("mTLS: accepted", "ALLOW reader + GET /orders"), allowed=True),
        peer("writer", decision=("mTLS: accepted", "403 · writer is not allowed"), allowed=False),
        peer("reader", decision=("STRICT: plaintext rejected", "No HTTP response"), allowed=False, plaintext=True),
    )),
    Example("peer-authorization", "permissive-identity", "PERMISSIVE does not grant a ServiceAccount identity", (
        peer("reader", decision=("mTLS: identity = shop/reader", "ALLOW → application"), allowed=True),
        peer("reader", decision=("Plaintext: no verified identity", "403 · ALLOW rule not matched"), allowed=False, plaintext=True),
        peer("writer", decision=("mTLS: identity = shop/writer", "403 · ALLOW rule not matched"), allowed=False),
    )),
    Example("peer-authorization", "deny-admin-write", "DENY wins over ALLOW", (
        peer("reader", "admin", decision=("DENY: not matched", "ALLOW: reader + GET /admin"), allowed=True),
        peer("reader", "admin", "POST", decision=("DENY: POST /admin", "403 · ALLOW cannot override"), allowed=False),
        peer("reader", "orders", "POST", decision=("DENY: not matched", "ALLOW: reader + POST /orders"), allowed=True),
    )),
    Example("request-authorization", "validate-only", "Validate JWT when present", (
        jwt("", ("No JWT: validation skipped", "No AuthorizationPolicy"), True),
        jwt("VALID", ("JWT signature / iss / aud / exp: OK", "No AuthorizationPolicy"), True),
        jwt("INVALID", ("JWT signature: invalid", "401 · rejected by Envoy"), False),
    )),
    Example("request-authorization", "require-token", "Require a valid JWT", (
        jwt("", ("No authenticated JWT principal", "403 · ALLOW rule not matched"), False),
        jwt("INVALID", ("JWT signature: invalid", "401 · authorization not reached"), False),
        jwt("VALID", ("JWT valid: principal exists", "ALLOW requestPrincipals: *"), True),
    )),
    Example("request-authorization", "admin-and-health", "Public health check + JWT role for orders", (
        jwt("", ("No JWT: validation skipped", "ALLOW GET /healthz"), True, "healthz"),
        jwt("ADMIN", ("JWT valid · role=admin", "ALLOW GET /orders"), True, claim="JWT claim: role=admin"),
        jwt("USER", ("JWT valid · role=user", "403 · admin role required"), False, claim="JWT claim: role=user"),
    )),
)


def summary(resource):
    kind, spec = resource["kind"], resource["spec"]
    selector = spec["workloadSelector"]["labels"] if kind == "Sidecar" else spec["selector"]["matchLabels"]
    label = selector["app"]
    lines = [f"namespace: {resource['metadata']['namespace']} · app={label}"]
    if kind == "Sidecar":
        lines.append("outboundTrafficPolicy: " + spec["outboundTrafficPolicy"]["mode"])
        lines.append("hosts: " + ", ".join(spec["egress"][0]["hosts"][:2]))
        lines.extend(spec["egress"][0]["hosts"][2:])
    elif kind == "PeerAuthentication":
        lines.append("mtls.mode: " + spec["mtls"]["mode"])
    elif kind == "RequestAuthentication":
        rule = spec["jwtRules"][0]
        lines.extend(["issuer: " + rule["issuer"], "audience: " + ", ".join(rule["audiences"]),
                      "JWKS: " + rule["jwksUri"]])
    else:
        lines.append("action: " + spec["action"])
        for rule in spec["rules"]:
            if len(spec["rules"]) > 1:
                operation = rule["to"][0]["operation"]
                route = ", ".join(operation["methods"]) + " " + ", ".join(operation["paths"])
                condition = "JWT role=" + rule["when"][0]["values"][0] if rule.get("when") else "no JWT required"
                lines.append(f"{route} · {condition}")
                continue
            for source in rule.get("from", []):
                source = source["source"]
                if "principals" in source:
                    principal = source["principals"][0].split("/")
                    lines.append(f"ServiceAccount: {principal[-3]}/{principal[-1]}")
                if "requestPrincipals" in source:
                    lines.append("JWT principal required")
            for target in rule.get("to", []):
                operation = target["operation"]
                lines.append(", ".join(operation["methods"]) + " " + ", ".join(operation["paths"]))
            for condition in rule.get("when", []):
                lines.append("JWT role: " + ", ".join(condition["values"]))
    return kind, lines


def draw(example, resources):
    panels = [summary(resource) for resource in resources]
    panel_height = max(58 + 31 * len(lines) + 16 for _, lines in panels)
    row_start = panel_height + 95
    c = Canvas((1640, row_start + 240 * len(example.cases) + 10))
    width = min(740, (1540 - 30 * (len(panels) - 1)) // len(panels))
    x = (1640 - len(panels) * width - (len(panels) - 1) * 30) // 2
    for title, lines in panels:
        c.card(x, 25, width, panel_height, title, lines, "neutral")
        x += width + 30
    for index, case in enumerate(example.cases):
        y = row_start + index * 240
        sidecar = example.topic == "sidecar"
        frame_x, frame_w = (40, 1100) if sidecar else (650, 960)
        c.box(frame_x, y, frame_w, 211, "white", BORDER)
        c.text(frame_x + 20, y + 13, f"Pod {case.source if sidecar else 'shop/api · app=api'}", 22, MUTED, True)
        if sidecar:
            c.text(1280, y + 13, f"Pod {case.target}", 22, MUTED, True)
        else:
            c.text(70, y + 13, f"Pod {case.source}", 22, MUTED, True)
        c.card(70, y + 48, 480, 150, "Container", case.command, "app")
        c.card(680, y + 48, 430, 150, "Envoy", case.decision, "proxy" if case.allowed else "blocked")
        c.card(1300, y + 48, 280, 150, "Envoy → API" if sidecar else "API", case.result if case.allowed else ("Not reached",),
               "target" if case.allowed else "neutral")
        center = y + 126
        # Gaps mark the boundary between containers and Pods.
        boundary = 1140 if sidecar else 650
        c.line([(boundary, center - 14), (boundary, center + 14)], "white", width=6)
        c.arrow([(550, center), (680, center)], BLUE)
        c.text(571, center - 33, "HTTP" if sidecar else case.transport, 21, BLUE)
        if case.allowed:
            c.arrow([(1110, center), (1300, center)], GREEN)
            c.text(1172, center - 33, case.transport if sidecar else "HTTP", 21, GREEN)
        else:
            c.line([(1110, center), (1190, center)], RED)
            c.line([(1182, center - 8), (1198, center + 8)], RED)
            c.line([(1182, center + 8), (1198, center - 8)], RED)
    return c.image


def update_image(path, image, check):
    if check:
        if not path.is_file():
            raise ValueError(f"Missing PNG: {path}")
        with Image.open(path) as old:
            if old.size != image.size or old.convert("RGB").tobytes() != image.tobytes():
                raise ValueError(f"Stale PNG: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "PNG", optimize=True)
    print(path.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    pages = {}
    for example in EXAMPLES:
        manifest = ROOT / example.topic / f"{example.slug}.yaml"
        source = manifest.read_text()
        resources = list(yaml.safe_load_all(source))
        output = ROOT / "images" / example.topic / f"{example.slug}.png"
        update_image(output, draw(example, resources), args.check)
        pages.setdefault(example.topic, []).extend([
            f"#### {example.title}", "```yaml\n" + source.rstrip() + "\n```",
            f"![{example.title}]({output.relative_to(ROOT).as_posix()})",
        ])
    for topic, parts in pages.items():
        output = ROOT / f"README.{topic}.md"
        content = "\n\n".join(parts) + "\n"
        if args.check:
            if not output.is_file() or output.read_text() != content:
                raise ValueError(f"Stale Markdown: {output}")
        else:
            output.write_text(content)
        print(output.name)
    if args.check:
        print("Nine PNGs and three topic pages match their YAML and renderer.")


if __name__ == "__main__":
    main()
