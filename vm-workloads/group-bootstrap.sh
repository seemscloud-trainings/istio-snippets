#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${CLUSTER_ID:?Set CLUSTER_ID to the installed mesh cluster ID}"
: "${ISTIOD_IP:?Set ISTIOD_IP to the reachable xDS/CA gateway IP}"
workload_namespace="$(kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}')"
workload_namespace="${workload_namespace:-default}"

for item in vm1:10.20.0.11 vm2:10.20.0.12 vm3:10.20.0.13; do
  vm_name="${item%%:*}"
  vm_ip="${item#*:}"
  istioctl x workload entry configure \
    --name shared-app --namespace "$workload_namespace" \
    --clusterID "$CLUSTER_ID" --ingressIP "$ISTIOD_IP" \
    --internalIP "$vm_ip" --autoregister \
    --revision "${ISTIO_REVISION:-}" --output ".local/vm-group/$vm_name"
done
