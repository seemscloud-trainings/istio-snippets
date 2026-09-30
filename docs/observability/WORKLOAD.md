# Workload — Nimbus observability labs

## Retries hide failures

**Metric:** `envoy_cluster_upstream_rq_retry`.

**Dashboard:** **Mesh Istio - Workload** → **Upstream retries per second**.

**Expected:** Retries increase; responses include HTTP 200 and 503.

```bash
kubectl delete -f labs/observability/nimbus/retry.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/retry.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/retry.yaml --ignore-not-found --wait=true
```

## Response deadline is too short

**Metric:** `envoy_cluster_upstream_rq_timeout`.

**Dashboard:** **Mesh Istio - Workload** → **Upstream timeouts per second**.

**Expected:** HTTP 504 after about 100 ms; the backend takes 3 seconds.

```bash
kubectl delete -f labs/observability/nimbus/timeout.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/timeout.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/timeout.yaml --ignore-not-found --wait=true
```

## Connection pool overflow

**Metric:** `envoy_cluster_upstream_rq_pending_overflow`.

**Dashboard:** **Mesh Istio - Workload** → **Pending request overflow per second**.

**Expected:** Excess requests return HTTP 503/UO; accepted requests take about 3 seconds.

```bash
kubectl delete -f labs/observability/nimbus/overflow.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/overflow.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/overflow.yaml --ignore-not-found --wait=true
```

## Application resets connections

**Metric:** `envoy_cluster_upstream_rq_rx_reset`.

**Dashboard:** **Mesh Istio - Workload** → **Request resets received per second**.

**Expected:** The backend resets connections; its inbound reset counter increases and clients receive HTTP 503.

```bash
kubectl delete -f labs/observability/nimbus/reset.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/reset.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/reset.yaml --ignore-not-found --wait=true
```

## Application memory exhaustion

**Metric:** `kube_pod_container_status_restarts_total`.

**Dashboard:** **Workload - Runtime** → **Restarts per interval**.

**Expected:** The app container exceeds 48 MiB and restarts with OOMKilled.

```bash
kubectl delete -f labs/observability/nimbus/oom.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/oom.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/oom.yaml --ignore-not-found --wait=true
```
