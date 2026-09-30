#!/usr/bin/env bash
set -euo pipefail
: "${ISTIO_VERSION:?Set ISTIO_VERSION to the matching istiod version}"
bootstrap="$(cd "${1:?Pass the copied bootstrap directory}" && pwd)"
if [[ "$EUID" -ne 0 ]]; then
  exec sudo env ISTIO_VERSION="$ISTIO_VERSION" bash "$0" "$bootstrap"
fi
[[ "$(dpkg --print-architecture)" == amd64 ]] || { echo 'This installer targets Debian/Ubuntu amd64.' >&2; exit 1; }
for file in cluster.env mesh.yaml istio-token root-cert.pem hosts; do
  [[ -s "$bootstrap/$file" ]] || { echo "Missing $bootstrap/$file" >&2; exit 1; }
done
apt-get update
apt-get install -y curl ca-certificates iptables iproute2 sudo
curl -fL "https://blob.istio.io/istio-release/releases/$ISTIO_VERSION/deb/istio-sidecar.deb" -o "$bootstrap/istio-sidecar.deb"
[[ "$(dpkg-deb -f "$bootstrap/istio-sidecar.deb" Architecture)" == amd64 ]]
dpkg -i "$bootstrap/istio-sidecar.deb"
install -d -o istio-proxy -g istio-proxy /etc/certs /etc/istio/config /etc/istio/proxy /var/lib/istio /var/lib/istio/envoy /var/run/secrets/tokens
install -o istio-proxy -g istio-proxy -m 0644 "$bootstrap/root-cert.pem" /etc/certs/root-cert.pem
install -o istio-proxy -g istio-proxy -m 0600 "$bootstrap/cluster.env" /var/lib/istio/envoy/cluster.env
install -o istio-proxy -g istio-proxy -m 0600 "$bootstrap/mesh.yaml" /etc/istio/config/mesh
install -o istio-proxy -g istio-proxy -m 0600 "$bootstrap/istio-token" /var/lib/istio/istio-token
install -o istio-proxy -g istio-proxy -m 0600 "$bootstrap/istio-token" /var/run/secrets/tokens/istio-token
hosts_tmp="$(mktemp)"
trap 'rm -f "$hosts_tmp"' EXIT
awk '/^# BEGIN ISTIO VM BOOTSTRAP$/{skip=1;next} /^# END ISTIO VM BOOTSTRAP$/{skip=0;next} !skip' /etc/hosts > "$hosts_tmp"
printf '\n# BEGIN ISTIO VM BOOTSTRAP\n' >> "$hosts_tmp"
cat "$bootstrap/hosts" >> "$hosts_tmp"
printf '\n# END ISTIO VM BOOTSTRAP\n' >> "$hosts_tmp"
cat "$hosts_tmp" > /etc/hosts
install -d /etc/systemd/system/istio.service.d
cat > /etc/systemd/system/istio.service.d/bootstrap-token.conf <<'UNIT'
[Service]
ExecStartPre=+/usr/bin/install -d -o istio-proxy -g istio-proxy -m 0700 /var/run/secrets/tokens
ExecStartPre=+/usr/bin/install -o istio-proxy -g istio-proxy -m 0600 /var/lib/istio/istio-token /var/run/secrets/tokens/istio-token
UNIT
systemctl daemon-reload
systemctl enable istio
systemctl restart istio
systemctl --no-pager --full status istio
