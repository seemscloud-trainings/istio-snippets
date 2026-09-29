#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${CLUSTER_ID:?Set CLUSTER_ID to the installed mesh cluster ID}"
: "${ISTIOD_IP:?Set ISTIOD_IP to the reachable xDS/CA gateway IP}"
workload_namespace="$(kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}')"
workload_namespace="${workload_namespace:-default}"

for item in orders:10.20.0.21:8080 payments:10.20.0.22:9090 inventory:10.20.0.23:7070; do
  IFS=: read -r app vm_ip app_port <<< "$item"
  output=".local/vm-entry/$app"
  mkdir -p "$output"
  istioctl x workload group create \
    --name "$app-vm" --namespace "$workload_namespace" \
    --labels "app=$app" --ports "http=$app_port" \
    --serviceAccount "$app" --network network1 > "$output/workloadgroup.yaml"
  istioctl x workload entry configure \
    --file "$output/workloadgroup.yaml" \
    --clusterID "$CLUSTER_ID" --ingressIP "$ISTIOD_IP" \
    --internalIP "$vm_ip" --autoregister=false \
    --revision "${ISTIO_REVISION:-}" --output "$output"
done
