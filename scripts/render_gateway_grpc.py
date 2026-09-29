#!/usr/bin/env python3
"""Render the supplied proxyless gRPC gateway example offline."""
import argparse
from pathlib import Path

from PIL import Image
import yaml
from render_service_entry import Canvas, BLUE, GREEN, MUTED
from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[1]


def render():
    c = Canvas((1800, 850))
    c.card(55, 25, 470, 175, 'VirtualService grpc',
           ['hosts: wp.pl', 'gateways: [gateway-green]', 'destination: grpc:9000'], 'neutral')
    c.card(675, 25, 490, 175, 'Gateway gateway-green',
           ['selector: istio=gateway-green', ':443 · TLS SIMPLE', 'credentialName: grpc-end-gw-tls'], 'neutral')
    c.arrow([(525, 112), (675, 112)], MUTED, True)
    c.text(555, 75, 'binding', 20, MUTED)
    c.arrow([(920, 200), (920, 300)], MUTED, True)
    c.card(55, 300, 470, 180, 'Client',
           ['grpcurl -cacert ca.crt', '-authority wp.pl', 'gateway-green:443 list'], 'app')
    c.card(675, 300, 490, 180, 'gateway-green / Envoy',
           ['TLS ends here · ALPN h2', 'Host / SNI: wp.pl', 'gRPC → Service grpc:9000'], 'proxy')
    c.card(1305, 300, 440, 180, 'grpc Pod / Application',
           ['HTTP/2 :9000 · no TLS', 'grpc-status: 0 (OK)', ':9443 not used by this route'], 'target')
    c.arrow([(525, 390), (675, 390)], BLUE)
    c.text(545, 350, 'TLS + h2', 20, BLUE)
    c.arrow([(1165, 390), (1305, 390)], GREEN)
    c.text(1180, 350, 'h2 :9000', 20, GREEN)
    c.card(1305, 25, 440, 175, 'grpc-agent',
           ['Istiod ↔ agent ↔ gRPC xDS', 'Bootstrap / configuration', 'No Envoy in the application Pod'], 'neutral')
    c.arrow([(1525, 200), (1525, 300)], MUTED, True)
    c.arrow([(1525, 480), (1525, 525), (290, 525), (290, 480)], GREEN)
    c.text(700, 540, 'Client ← grpc-status: 0 (OK)', 22, GREEN)
    c.card(55, 640, 470, 150, 'Client',
           ['grpcurl -plaintext', '-authority wp.pl gateway-green:80 list'], 'app')
    c.card(675, 640, 490, 150, 'gateway-green / Envoy',
           ['HTTP 301 → https://wp.pl/...', 'Use TLS :443 for gRPC'], 'blocked')
    c.card(1305, 640, 440, 150, 'grpc Pod / Application',
           ['Request not forwarded'], 'neutral')
    c.arrow([(525, 715), (675, 715)], BLUE)
    return c.image


def docs():
    sections = ['#### gRPC']
    for name in ('app', 'gateway'):
        resources = yaml.safe_load_all((ROOT / 'gateway-grpc' / f'{name}.yaml').read_text())
        sections.append('```yaml\n' + dump_documents(resources).strip() + '\n```')
    sections.extend([
        '![gRPC gateway: TLS termination, HTTP/2 backend and plaintext redirect](images/gateway-grpc/flow.png)',
        '#### TLS Secret',
        '```bash\nkubectl create secret tls grpc-end-gw-tls --cert=wp.pl.crt --key=wp.pl.key --dry-run=client -o yaml | kubectl apply -f -\nkubectl apply -f gateway-grpc/app.yaml -f gateway-grpc/gateway.yaml\n```',
        '#### Request',
        '```bash\ngrpcurl -cacert ca.crt -authority wp.pl gateway-green:443 list\n```',
    ])
    return '\n\n'.join(sections) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = ROOT / 'images/gateway-grpc/flow.png'
    page = ROOT / 'GATEWAY-GRPC.md'
    picture = render()
    if args.check:
        with Image.open(output) as old:
            assert old.size == picture.size and old.convert('RGB').tobytes() == picture.tobytes()
        assert page.read_text() == docs()
        print('gRPC guide and diagram match their sources.')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        picture.save(output, optimize=True)
        page.write_text(docs())


if __name__ == '__main__':
    main()
