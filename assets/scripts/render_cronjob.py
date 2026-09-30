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


def render(legacy=False):
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
    if legacy:
        rows = [
            ('Success', ['Classic sidecar · nativeSidecar: false', 'holdApplicationUntilProxyStarts', 'Envoy ready → start job'],
             ['curl https://wp.pl → exit 0', 'EXIT trap → POST :15020/quitquitquit', 'Application keeps exit 0'],
             ['Agent stops Envoy and exits', 'Pod: Succeeded', 'Job: Complete'], False),
            ('Without quitquitquit', ['Classic sidecar still running'],
             ['Application already exited 0', 'No shutdown request'],
             ['Pod stays Running', 'Job cannot complete', '120 s deadline → Job Failed'], True),
            ('Request fails', ['Envoy ready → start job'],
             ['curl --fail https://wp.pl', 'HTTP 500 → exit 22', 'EXIT trap → POST :15020/quitquitquit', 'Application keeps exit 22'],
             ['Agent stops Envoy and exits', 'Job: Failed · backoffLimit: 0', 'Failure is not changed to success'], True),
        ]
    for i, (title, proxy, app, result, problem) in enumerate(rows):
        y = 30 + i * 275
        c.text(50, y, title, 24, MUTED, True)
        c.card(50, y + 45, 490, 180, 'Envoy sidecar' if legacy else 'Envoy startup', proxy, 'blocked' if i == 1 else 'proxy')
        c.card(680, y + 45, 470, 180, 'Job container', app,
               'neutral' if i == 1 else 'blocked' if problem else 'app')
        c.card(1300, y + 45, 450, 180, 'Pod / Job lifecycle', result, 'blocked' if problem else 'target')
        c.arrow([(540, y + 130), (680, y + 130)], BLUE)
        c.text(556, y + 94, ('job done' if legacy else 'wait') if i == 1 else 'start', 20, BLUE)
        c.arrow([(1150, y + 130), (1300, y + 130)], GREEN)
    return c.image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    resource = yaml.safe_load((ASSETS / 'cronjob/native-sidecar.yaml').read_text())
    legacy = yaml.safe_load((ASSETS / 'cronjob/quitquitquit.yaml').read_text())
    content = '\n\n'.join([
        '#### CronJob · native sidecar · Kubernetes 1.33+',
        '```yaml\n' + dump_documents([resource]).strip() + '\n```',
        '#### Istiod Helm · startup probe',
        '```yaml\nglobal:\n  proxy:\n    startupProbe:\n      enabled: true\n```',
        '![CronJob: proxy readiness, successful completion and request failure](../../assets/images/cronjob/native-sidecar.png)',
        '#### CronJob · classic sidecar + quitquitquit',
        '```yaml\n' + dump_documents([legacy]).strip() + '\n```',
        '![CronJob: quitquitquit on success and failure](../../assets/images/cronjob/quitquitquit.png)',
    ]) + '\n'
    page = ROOT / "docs/configurations" / 'CRONJOB.md'
    for is_legacy, name in [(False, 'native-sidecar'), (True, 'quitquitquit')]:
        output = ASSETS / 'images/cronjob' / (name + '.png')
        picture = render(is_legacy)
        if args.check:
            with Image.open(output) as old:
                assert old.size == picture.size and old.convert('RGB').tobytes() == picture.tobytes()
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            picture.save(output, optimize=True)
    if args.check:
        assert page.read_text() == content
        print('Both CronJob examples and diagrams match their sources.')
    else:
        page.write_text(content)


if __name__ == '__main__':
    main()
