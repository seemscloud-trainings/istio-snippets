#!/usr/bin/env bash
set -euo pipefail
lab_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
kubectl delete jobs -n playground-nimbus-istio-enabled -l observability-lab=nimbus --ignore-not-found --wait=true
kubectl apply -k "$lab_dir"
