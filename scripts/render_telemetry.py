#!/usr/bin/env python3
"""Render a compact Telemetry example offline."""
import argparse
from pathlib import Path

from PIL import Image
import yaml
from render_service_entry import Canvas, BLUE, GREEN, MUTED
from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[1]


def render(resource):
    spec = resource['spec']
    sampling = spec['tracing'][0]['randomSamplingPercentage']
    c = Canvas((1800, 1070))
    rows = [
        ('Access logs · 200', ['curl http://wp.pl', 'Response: 200'],
         [spec['accessLogging'][0]['filter']['expression'], '200 does not match'],
         'stdout / access log', ['No access log for this request'], False, False),
        ('Access logs · 500', ['curl http://wp.pl', 'Response: 500'],
         [spec['accessLogging'][0]['filter']['expression'], '500 matches'],
         'stdout / access log', ['One error request logged', 'Client still receives 500'], True, True),
        ('Metrics', ['curl http://wp.pl', 'Response: 200 or 500'],
         ['SERVER · REQUEST_COUNT enabled', 'istio_requests_total +1', 'response_code="200" or "500"'],
         'Prometheus', ['Scrapes Envoy metrics', '200 and 500 counted separately', 'Log filter does not filter metrics'], True, False),
        ('Tracing', ['curl http://wp.pl', 'No prior sampling decision'],
         [f'randomSamplingPercentage: {sampling}', f'About {sampling}% selected for tracing', 'Earlier sampling decision is kept'],
         'otel → Alloy :4317', ['Selected request → span', 'Unselected request → no span', 'Application forwards trace headers'], True, False),
    ]
    for i, (title, client, proxy, sink, result, emitted, error) in enumerate(rows):
        y = 35 + i * 260
        c.text(55, y, title, 24, MUTED, True)
        c.card(55, y + 45, 465, 165, 'Client Pod / Container', client, 'app')
        c.card(670, y + 45, 505, 165, 'Server Envoy', proxy, 'blocked' if error else 'proxy')
        c.card(1315, y + 45, 430, 165, sink, result, 'target' if emitted else 'neutral')
        c.arrow([(520, y + 125), (670, y + 125)], BLUE)
        c.text(550, y + 91, 'request', 20, BLUE)
        if emitted:
            if i == 2:
                c.arrow([(1315, y + 125), (1175, y + 125)], GREEN, True)
                c.text(1210, y + 91, 'scrape', 20, GREEN)
            else:
                c.arrow([(1175, y + 125), (1315, y + 125)], GREEN)
        else:
            c.line([(1175, y + 125), (1250, y + 125)], MUTED)
            c.line([(1242, y + 117), (1258, y + 133)], MUTED)
            c.line([(1242, y + 133), (1258, y + 117)], MUTED)
    return c.image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    resource = yaml.safe_load((ROOT / 'telemetry/default.yaml').read_text())
    content = '\n\n'.join([
        '#### Access logs + metrics + tracing',
        '```yaml\n' + dump_documents([resource]).strip() + '\n```',
        '![Telemetry: error logs, request counters and trace sampling](images/telemetry/default.png)',
    ]) + '\n'
    page = ROOT / 'TELEMETRY.md'
    output = ROOT / 'images/telemetry/default.png'
    picture = render(resource)
    if args.check:
        assert page.read_text() == content
        with Image.open(output) as old:
            assert old.size == picture.size and old.convert('RGB').tobytes() == picture.tobytes()
        print('Telemetry YAML, page and diagram match.')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        picture.save(output, optimize=True)
        page.write_text(content)


if __name__ == '__main__':
    main()
