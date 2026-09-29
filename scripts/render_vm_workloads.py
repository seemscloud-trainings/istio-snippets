#!/usr/bin/env python3
"""Render the two VM integration cases; never execute their bootstrap/install scripts."""
import argparse
from pathlib import Path

from PIL import Image
import yaml

from render_service_entry import Canvas, BLUE, GREEN, MUTED, BORDER
from yaml_style import dump_documents

ROOT = Path(__file__).resolve().parents[1]
VM = ROOT / "vm-workloads"


def render(manual):
    c = Canvas((1800, 1390))
    if manual:
        first_title = "WorkloadEntry ×3"
        first = ["orders-vm / payments-vm / inventory-vm", "Created explicitly with kubectl", "No auto-registration"]
        control = ["Registry: 3 separate applications", "xDS + certificates"]
        services = ["orders.wp.pl → app=orders → VM1 :8080", "payments.wp.pl → app=payments → VM2 :9090", "inventory.wp.pl → app=inventory → VM3 :7070"]
        rows = [
            ("orders.wp.pl", "orders", "VM1", "10.20.0.21", 8080, False),
            ("payments.wp.pl", "payments", "VM2", "10.20.0.22", 9090, False),
            ("inventory.wp.pl", "inventory", "VM3", "10.20.0.23", 7070, False),
            ("orders.wp.pl", "orders", "VM1", "10.20.0.21", 8080, True),
        ]
    else:
        first_title = "WorkloadGroup shared-app"
        first = ["app=shared-app · SA=shared-app", "HTTP :8080 · network1", "TCP readiness: 5 s / 2 failures"]
        control = ["--autoregister → 3 WorkloadEntries", "xDS + certificates"]
        services = ["wp.pl → app=shared-app → VM1 / VM2 / VM3", "STATIC · ROUND_ROBIN · ISTIO_MUTUAL", "After readiness update: exclude unhealthy VM"]
        rows = [("wp.pl", "shared-app", f"VM{i}", f"10.20.0.{10+i}", 8080, False) for i in (1, 2, 3)]
        rows.append(("wp.pl", "shared-app", "VM2", "10.20.0.12", 8080, True))
    c.card(60, 25, 500, 175, first_title, first, "neutral")
    c.card(650, 25, 500, 175, "Istiod", control, "proxy")
    c.card(1250, 25, 500, 175, "VM agents", ["VM1 / VM2 / VM3", "systemd: istio"], "neutral")
    c.arrow([(560, 110), (650, 110)], BLUE, True)
    c.text(572, 75, "config", 18, BLUE)
    c.arrow([(1250, 110), (1150, 110)], BLUE, True)
    c.text(1166, 75, "15012", 18, BLUE)
    c.card(350, 235, 1100, 175, "ServiceEntry + DestinationRule", services, "neutral")
    for index, (host, app, vm, ip, port, problem) in enumerate(rows):
        y = 450 + index * 230
        c.box(40, y, 1100, 210, "white", BORDER)
        c.box(1260, y, 510, 210, "white", BORDER)
        c.text(60, y + 12, "Pod client", 22, MUTED, True)
        c.text(1280, y + 12, f"{vm} · {ip}", 22, MUTED, True)
        vip = {"orders": "198.51.100.101", "payments": "198.51.100.102", "inventory": "198.51.100.103"}.get(app, "198.51.100.100")
        c.card(65, y + 48, 480, 145, "Container", [f"curl http://{host}", f"DNS → {vip}"], "app")
        route = [f"ServiceEntry: app={app}", f"{vm}: {ip}:{port}"]
        target = [f"mTLS :{port} → HTTP :{port}", "Application → 200"]
        if problem:
            if manual:
                route = ["orders-vm still registered", "Connect fails → client gets 503"]
                target = [f"TCP :{port} refused", "Application not reached"]
            else:
                route = ["VM1: NotReady → excluded", f"Select {vm}: {ip}:{port}"]
        c.card(680, y + 48, 430, 145, "Envoy", route, "blocked" if problem else "proxy")
        c.card(1290, y + 48, 450, 145, "Envoy → Application", target,
               "blocked" if problem and manual else "target")
        mid = y + 126
        for edge in (1140, 1260):
            c.line([(edge, mid - 14), (edge, mid + 14)], "white", width=6)
        c.arrow([(545, mid), (680, mid)], BLUE)
        c.text(563, mid - 33, "HTTP :80", 20, BLUE)
        if problem and manual:
            c.line([(1110, mid), (1190, mid)], "#a34740")
            c.line([(1182, mid - 8), (1198, mid + 8)], "#a34740")
            c.line([(1182, mid + 8), (1198, mid - 8)], "#a34740")
        else:
            c.arrow([(1110, mid), (1290, mid)], GREEN)
            c.text(1170, mid - 33, "mTLS", 20, GREEN)
    return c.image


def code(language, text):
    return f"```{language}\n{text.strip()}\n```"


def script(name):
    lines = (VM / name).read_text().splitlines()
    return "\n".join(lines[1:])


def docs():
    parts = [
        "## 1. WorkloadGroup — one application on three VMs",
        "Debian/Ubuntu amd64; applications already listen on 8080. One routable L3 network (`network1`): Pods ↔ VM application ports, VM → Istiod gateway on TCP 15012. The selected namespace is already managed by Istio; its `istio-ca-root-cert` ConfigMap exists. Istiod needs `PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION=true` and `PILOT_ENABLE_WORKLOAD_ENTRY_HEALTHCHECKS=true`.",
        "**Workstation** — use the matching Istio release and replace these example gateway/cluster values; use your workload namespace in the current kubectl context.",
        code("bash", """export ISTIO_VERSION=1.30.5
export CLUSTER_ID=cluster1
export ISTIOD_IP=192.0.2.10
export ISTIO_REVISION=green
export VM_USER=ubuntu
istioctl version --remote=false"""),
        "Use an empty `ISTIO_REVISION` for an unrevisioned control plane. The 15012 gateway must forward to the selected Istiod revision; network IDs must match the existing mesh.",
        code("yaml", dump_documents(yaml.safe_load_all((VM / "workload-group.yaml").read_text()))),
        "![WorkloadGroup: one service, three VM instances](images/vm-workloads/workload-group.png)",
        "**Register and generate one bundle per VM** — WorkloadGroup is stored in Kubernetes; WorkloadEntries appear when the VM agents connect. `workloadSelector` here binds VM endpoints to ServiceEntry.",
        code("bash", "kubectl apply -f vm-workloads/workload-group.yaml"),
        code("bash", script("group-bootstrap.sh")),
        "The same commands are saved in [group-bootstrap.sh](vm-workloads/group-bootstrap.sh).",
        "| Generated file | On the VM |\n|---|---|\n| `cluster.env` | `/var/lib/istio/envoy/cluster.env` — IP, ports, identity, network |\n| `mesh.yaml` | `/etc/istio/config/mesh` — discovery/proxy configuration |\n| `root-cert.pem` | `/etc/certs/root-cert.pem` — CA trust |\n| `istio-token` | `/var/lib/istio/istio-token` → `/var/run/secrets/tokens/istio-token` |\n| `hosts` | Managed block in `/etc/hosts` — reachable Istiod address |",
        "**Copy** — `VM_USER` is your SSH user; each VM gets its own bundle.",
        code("bash", """for item in vm1:10.20.0.11 vm2:10.20.0.12 vm3:10.20.0.13; do
  vm_name="${item%%:*}"
  vm_ip="${item#*:}"
  ssh "$VM_USER@$vm_ip" 'mkdir -p "$HOME/istio-bootstrap"; chmod 700 "$HOME/istio-bootstrap"'
  scp ".local/vm-group/$vm_name/"{cluster.env,mesh.yaml,root-cert.pem,istio-token,hosts} \\
    vm-workloads/install-vm.sh "$VM_USER@$vm_ip:istio-bootstrap/"
done"""),
        "**On each VM** — [install-vm.sh](vm-workloads/install-vm.sh) installs the official `istio-sidecar` package, copies the five files, configures token restoration after reboot, and starts the `istio` systemd service.",
        code("bash", """export ISTIO_VERSION=1.30.5
sudo env ISTIO_VERSION="$ISTIO_VERSION" bash "$HOME/istio-bootstrap/install-vm.sh" "$HOME/istio-bootstrap"
sudo systemctl status istio --no-pager
curl -fsS http://127.0.0.1:15021/healthz/ready"""),
        "**Check from the workstation** — create the client after ProxyConfig so DNS capture is enabled.",
        code("bash", """kubectl get workloadentry -l app=shared-app -o wide
istioctl proxy-status
kubectl run vm-client --image=curlimages/curl:8.16.0 --restart=Never --command -- sleep 3600
kubectl wait pod/vm-client --for=condition=Ready --timeout=120s
kubectl exec vm-client -c vm-client -- curl -sS http://wp.pl"""),
        "The bootstrap token defaults to one hour. Renew it before expiry and update both token paths on the matching VM; restoring a file after reboot does not renew it. Generated bundles stay in Git-ignored `.local/`.",
        code("bash", "kubectl create token shared-app --audience=istio-ca --duration=1h > .local/vm-group/vm1/istio-token"),
        "## 2. WorkloadEntry — three applications on three VMs",
        "Same prerequisites and installation steps. VM1: orders on `10.20.0.21:8080`; VM2: payments on `10.20.0.22:9090`; VM3: inventory on `10.20.0.23:7070`. Each application has its own ServiceAccount, WorkloadEntry and ServiceEntry.",
        code("yaml", dump_documents(yaml.safe_load_all((VM / "workload-entry.yaml").read_text()))),
        "![WorkloadEntry: three separate VM services](images/vm-workloads/workload-entry.png)",
        "**Register and bootstrap** — the WorkloadGroup files below are local `istioctl` input only; do not apply them. `--autoregister=false` keeps the three WorkloadEntries manually managed.",
        code("bash", "kubectl apply -f vm-workloads/workload-entry.yaml"),
        code("bash", script("entry-bootstrap.sh")),
        "The same commands are saved in [entry-bootstrap.sh](vm-workloads/entry-bootstrap.sh).",
        "**Copy and install** — the generated files and their VM destinations are identical to case 1.",
        code("bash", """for item in orders:10.20.0.21 payments:10.20.0.22 inventory:10.20.0.23; do
  app="${item%%:*}"
  vm_ip="${item#*:}"
  ssh "$VM_USER@$vm_ip" 'mkdir -p "$HOME/istio-bootstrap"; chmod 700 "$HOME/istio-bootstrap"'
  scp ".local/vm-entry/$app/"{cluster.env,mesh.yaml,root-cert.pem,istio-token,hosts} \\
    vm-workloads/install-vm.sh "$VM_USER@$vm_ip:istio-bootstrap/"
done"""),
        code("bash", """export ISTIO_VERSION=1.30.5
sudo env ISTIO_VERSION="$ISTIO_VERSION" bash "$HOME/istio-bootstrap/install-vm.sh" "$HOME/istio-bootstrap"
curl -fsS http://127.0.0.1:15021/healthz/ready"""),
        "**Check** — reuse `vm-client` from case 1, or create it with the same command.",
        code("bash", """kubectl get workloadentry orders-vm payments-vm inventory-vm -o wide
istioctl proxy-status
kubectl exec vm-client -c vm-client -- curl -sS http://orders.wp.pl
kubectl exec vm-client -c vm-client -- curl -sS http://payments.wp.pl
kubectl exec vm-client -c vm-client -- curl -sS http://inventory.wp.pl"""),
        "Renew each VM token using its own ServiceAccount (`orders`, `payments`, `inventory`). A stopped VM does not remove a manually created WorkloadEntry.",
    ]
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for manual, name in ((False, "workload-group"), (True, "workload-entry")):
        output = ROOT / "images/vm-workloads" / f"{name}.png"
        image = render(manual)
        if args.check:
            with Image.open(output) as old:
                if old.size != image.size or old.convert("RGB").tobytes() != image.tobytes():
                    raise ValueError(f"Stale PNG: {output}")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, "PNG", optimize=True)
    page = ROOT / "README.vm-workloads.md"
    content = docs()
    if args.check:
        if page.read_text() != content:
            raise ValueError("Stale VM guide")
        print("Two VM diagrams and guide match their sources.")
    else:
        page.write_text(content)
        print(page.name)


if __name__ == "__main__":
    main()
