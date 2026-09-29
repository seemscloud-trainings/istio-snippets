#!/usr/bin/env python3
"""Render gateway-blue HTTPS and HTTP redirect offline."""
import argparse
from pathlib import Path

from PIL import Image
import yaml
from render_service_entry import Canvas, BLUE, GREEN, MUTED
from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[1]


def render(resources):
    gateway, virtual = resources
    name = gateway['metadata']['name']
    workload = gateway['spec']['selector']['istio']
    c = Canvas((1700, 950))
    c.card(50, 30, 470, 145, 'VirtualService ' + name,
           ['hosts: wp.pl', 'gateways: [' + virtual['spec']['gateways'][0] + ']'], 'neutral')
    c.card(670, 30, 470, 205, 'Gateway ' + name,
           ['selector: istio=' + workload, 'HTTPS :443 · TLS SIMPLE',
            'Secret: wp-pl-tls · certificate: wp.pl', 'HTTP :80 → HTTPS :443'], 'neutral')
    c.arrow([(520, 100), (670, 100)], MUTED, True)
    c.text(550, 66, 'binding', 20, MUTED)
    c.arrow([(905, 235), (905, 320)], MUTED, True)
    c.text(920, 260, 'selects Pod', 20, MUTED)
    c.card(50, 320, 470, 180, 'Client Pod / Container',
           ['curl --connect-to', 'wp.pl:443:' + workload + ':443', 'https://wp.pl/test/cosmos-healthy'], 'app')
    c.card(670, 320, 470, 180, workload + ' / Envoy',
           ['TLS ends here · Host: wp.pl', 'VirtualService ' + name, 'route → playground-trouble:80'], 'proxy')
    c.card(1270, 320, 380, 180, 'Backend Pod',
           ['Envoy → playground-trouble', '/test/cosmos-healthy', 'Application → 200'], 'target')
    c.arrow([(520, 410), (670, 410)], BLUE)
    c.text(545, 375, 'TLS :443', 20, BLUE)
    c.arrow([(1140, 410), (1270, 410)], GREEN)
    c.text(1162, 375, 'route', 20, GREEN)
    c.arrow([(1460, 500), (1460, 570), (1010, 570), (1010, 500)], GREEN)
    c.text(1170, 585, 'Backend → Gateway: 200', 20, GREEN)
    c.arrow([(800, 500), (800, 570), (285, 570), (285, 500)], GREEN)
    c.text(360, 585, 'Gateway → Client: 200', 20, GREEN)
    c.card(50, 680, 470, 165, 'Client Pod / Container',
           ['curl --connect-to', 'wp.pl:80:' + workload + ':80', 'http://wp.pl/test/cosmos-healthy'], 'app')
    c.card(670, 680, 470, 165, workload + ' / Envoy',
           ['HTTP 301', 'Location:', 'https://wp.pl/test/cosmos-healthy'], 'proxy')
    c.card(1270, 680, 380, 165, 'Backend Pod', ['Request not forwarded'], 'neutral')
    c.arrow([(520, 760), (670, 760)], BLUE)
    c.text(545, 725, 'HTTP :80', 20, BLUE)
    c.arrow([(905, 845), (905, 885), (285, 885), (285, 845)], GREEN)
    c.text(420, 905, 'Gateway → Client: 301', 20, GREEN)
    return c.image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    sections = []
    for color in ('blue',):
        resources = list(yaml.safe_load_all((ROOT / 'gateway' / f'{color}.yaml').read_text()))
        output = ROOT / 'images/gateway' / f'{color}.png'
        picture = render(resources)
        if args.check:
            with Image.open(output) as existing:
                assert existing.size == picture.size and existing.convert('RGB').tobytes() == picture.tobytes(), output
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            picture.save(output, optimize=True)
        sections.extend([
            f'#### gateway-{color}',
            '```yaml\n' + dump_documents(resources).strip() + '\n```',
            f'![Gateway {color} binding and request flow](images/gateway/{color}.png)',
        ])
    content = '\n\n'.join(sections) + '\n'
    page = ROOT / 'GATEWAY.md'
    if args.check:
        assert page.read_text() == content, page
        print('Gateway-blue HTTPS and redirect diagram match the manifest.')
    else:
        page.write_text(content)


if __name__ == '__main__':
    main()
