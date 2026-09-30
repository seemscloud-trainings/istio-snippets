#!/usr/bin/env python3
"""Render CronJob native sidecar lifecycle offline."""
import argparse
from pathlib import Path

from PIL import Image
import yaml
from render_service_entry import Canvas, BLUE, GREEN, MUTED
from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"


def render():
    c = Canvas((1800, 850))
    rows = [
        ('Success', ['istio-proxy in initContainers', 'restartPolicy: Always', 'startupProbe → ready'],
         ['curl https://wp.pl', 'HTTP 200 → exit 0'],
         ['Kubelet stops sidecar', 'Pod: Succeeded', 'Job: Complete'], False),
        ('Proxy not ready', ['startupProbe not ready', 'Application waits'],
         ['curl has not started', 'No request sent'],
         ['Ready before deadline → run job', '120 s deadline → Job Failed'], True),
        ('Request fails', ['startupProbe → ready'],
         ['curl --fail https://wp.pl', 'HTTP 500 → exit 22'],
         ['Kubelet stops sidecar', 'Job: Failed · backoffLimit: 0', 'No retry of this Job'], True),
    ]
    for i, (title, proxy, app, result, problem) in enumerate(rows):
        y = 30 + i * 275
        c.text(50, y, title, 24, MUTED, True)
        c.card(50, y + 45, 490, 180, 'Envoy startup', proxy, 'blocked' if i == 1 else 'proxy')
        c.card(680, y + 45, 470, 180, 'Job container', app,
               'neutral' if i == 1 else 'blocked' if problem else 'app')
        c.card(1300, y + 45, 450, 180, 'Pod / Job lifecycle', result, 'blocked' if problem else 'target')
        c.arrow([(540, y + 130), (680, y + 130)], BLUE)
        c.text(566, y + 94, 'wait' if i == 1 else 'start', 20, BLUE)
        c.arrow([(1150, y + 130), (1300, y + 130)], GREEN)
    return c.image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    resource = yaml.safe_load((ASSETS / 'cronjob/native-sidecar.yaml').read_text())
    content = '\n\n'.join([
        '#### CronJob · native sidecar · Kubernetes 1.33+',
        '```yaml\n' + dump_documents([resource]).strip() + '\n```',
        '#### Istiod Helm · startup probe',
        '```yaml\nglobal:\n  proxy:\n    startupProbe:\n      enabled: true\n```',
        '![CronJob: proxy readiness, successful completion and request failure](../../assets/images/cronjob/native-sidecar.png)',
    ]) + '\n'
    page = ROOT / "docs/components" / 'CRONJOB.md'
    output = ASSETS / 'images/cronjob/native-sidecar.png'
    picture = render()
    if args.check:
        assert page.read_text() == content
        with Image.open(output) as old:
            assert old.size == picture.size and old.convert('RGB').tobytes() == picture.tobytes()
        print('CronJob page and diagram match their sources.')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        picture.save(output, optimize=True)
        page.write_text(content)


if __name__ == '__main__':
    main()
