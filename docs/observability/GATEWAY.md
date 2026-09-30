# Gateway — Nimbus observability labs

## Gateway Unhealthy

**Metric:** `envoy_cluster_upstream_cx_none_healthy`.

**Dashboard:** **Mesh Istio - Gateway** → **No healthy upstream per second**.

**Expected:** HTTP 503/UH: the selected subset has no healthy endpoints.

```bash
kubectl delete -f labs/observability/nimbus/gateway-unhealthy.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-unhealthy.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/gateway-unhealthy.yaml --ignore-not-found --wait=true
```

## Gateway Tls

**Metric:** `envoy_cluster_upstream_cx_connect_fail`.

**Dashboard:** **Mesh Istio - Gateway** → **Connection failures per second**.

**Expected:** HTTP 503/UF: TLS negotiation fails against the plaintext HTTP backend.

```bash
kubectl delete -f labs/observability/nimbus/gateway-tls.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-tls.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/gateway-tls.yaml --ignore-not-found --wait=true
```

## Gateway Overflow

**Metric:** `envoy_cluster_upstream_rq_pending_overflow`.

**Dashboard:** **Mesh Istio - Gateway** → **Pending request overflow per second**.

**Expected:** Excess concurrent requests return HTTP 503/UO.

```bash
kubectl delete -f labs/observability/nimbus/gateway-overflow.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-overflow.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/gateway-overflow.yaml --ignore-not-found --wait=true
```

## Gateway Reject

**Metric:** `envoy_cluster_manager_cds_update_rejected`.

**Dashboard:** **Mesh Istio - Gateway** → **CDS updates rejected per interval**.

**Expected:** Envoy rejects the invalid cluster configuration; the CDS rejection counter increases.

```bash
kubectl delete -f labs/observability/nimbus/gateway-reject.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-reject.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/gateway-reject.yaml --ignore-not-found --wait=true
```

## Gateway Pressure

**Metric:** `container_cpu_cfs_throttled_seconds_total`.

**Dashboard:** **Workload - Runtime** → **Throttled CPU time per second**.

**Expected:** Gateway CPU throttling increases under concurrent traffic.

```bash
kubectl delete -f labs/observability/nimbus/gateway-pressure.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-pressure.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/gateway-pressure.yaml --ignore-not-found --wait=true
```

## Gateway Warming

**Metric:** `envoy_listener_manager_total_listeners_warming`.

**Dashboard:** **Mesh Istio - Gateway** → **Warming listeners**.

**Expected:** The HTTPS listener remains warming because its TLS Secret is missing.

```bash
kubectl delete -f labs/observability/nimbus/gateway-warming.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-warming.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/gateway-warming.yaml --ignore-not-found --wait=true
```
