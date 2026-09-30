# Workload — Nimbus observability labs

All YAML files include namespaces. Run from the repository root with a cluster-admin context; participant RBAC does not allow every resource. Run one scenario at a time. These files are intentionally faulty and must not be added to an auto-sync repository.

Each traffic Job waits 30 seconds, runs 20 workers for 180 seconds, and stops after at most 240 seconds. Native Istio sidecars let Jobs complete. Re-applying a completed Job does not rerun it: the command below deletes only that scenario before recreating it. Never use `kubectl apply -f labs/observability/nimbus/`.

Prometheus scrapes Istiod/Envoy every 15 seconds. Select Last 15 minutes, refresh 15 seconds, and wait 30–60 seconds. Error counters are viewed as rates/increases, not raw totals.

## Retries hide failures

Automatic traffic for 180 seconds after a 30-second startup delay.

- **Metric:** `envoy_cluster_upstream_rq_retry`.
- **Dashboard:** **Mesh Istio - Workload** → **Upstream retries per second**.
- **Filter:** namespace `playground-nimbus-istio-enabled`, Pod `obs-retry-traffic-*`; select all upstream clusters, then narrow to `obs-`.

**Expected:** A mix of final 200/503 responses and a rising retry counter. Backend responses alternate probabilistically with time; exact proportions are not guaranteed.

[Open complete YAML](../../labs/observability/nimbus/retry.yaml)

```bash
kubectl delete -f labs/observability/nimbus/retry.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/retry.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/retry.yaml)

```bash
kubectl delete -f labs/observability/nimbus/retry.yaml --ignore-not-found --wait=true
```

## Response deadline is too short

Automatic traffic for 180 seconds after a 30-second startup delay.

- **Metric:** `envoy_cluster_upstream_rq_timeout`.
- **Dashboard:** **Mesh Istio - Workload** → **Upstream timeouts per second**.
- **Filter:** namespace `playground-nimbus-istio-enabled`, Pod `obs-timeout-traffic-*`; select all upstream clusters, then narrow to `obs-`.

**Expected:** 504 responses after roughly 100 ms despite the backend sleeping 3 seconds.

[Open complete YAML](../../labs/observability/nimbus/timeout.yaml)

```bash
kubectl delete -f labs/observability/nimbus/timeout.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/timeout.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/timeout.yaml)

```bash
kubectl delete -f labs/observability/nimbus/timeout.yaml --ignore-not-found --wait=true
```

## Connection pool overflow

Automatic traffic for 180 seconds after a 30-second startup delay.

- **Metric:** `envoy_cluster_upstream_rq_pending_overflow`.
- **Dashboard:** **Mesh Istio - Workload** → **Pending request overflow per second**.
- **Filter:** namespace `playground-nimbus-istio-enabled`, Pod `obs-overflow-traffic-*`; select all upstream clusters, then narrow to `obs-`.

**Expected:** Excess concurrent requests return 503/UO; admitted requests take about 3 seconds.

[Open complete YAML](../../labs/observability/nimbus/overflow.yaml)

```bash
kubectl delete -f labs/observability/nimbus/overflow.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/overflow.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/overflow.yaml)

```bash
kubectl delete -f labs/observability/nimbus/overflow.yaml --ignore-not-found --wait=true
```

## Application resets connections

Automatic traffic for 180 seconds after a 30-second startup delay.

- **Metric:** `envoy_cluster_upstream_rq_rx_reset`.
- **Dashboard:** **Mesh Istio - Workload** → **Request resets received per second**.
- **Filter:** namespace `playground-nimbus-istio-enabled`, Pod `obs-reset-*` (backend Deployment, not traffic Job); select upstream cluster `inbound|8080||` for socket resets.

**Expected:** The backend resets sockets; inspect inbound resets on the backend proxy, while the client commonly receives 503.

[Open complete YAML](../../labs/observability/nimbus/reset.yaml)

```bash
kubectl delete -f labs/observability/nimbus/reset.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/reset.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/reset.yaml)

```bash
kubectl delete -f labs/observability/nimbus/reset.yaml --ignore-not-found --wait=true
```

## Application memory exhaustion

Automatic traffic for 180 seconds after a 30-second startup delay.

- **Metric:** `kube_pod_container_status_restarts_total`.
- **Dashboard:** **Workload - Runtime** → **Restarts per interval**.
- **Filter:** namespace `playground-nimbus-istio-enabled`, Pod `obs-oom-*`; select all upstream clusters, then narrow to `obs-`.

**Expected:** The application allocates memory after 20 seconds, reaches its 48 MiB limit and restarts. Select container app; the sidecar is not the allocation target.

[Open complete YAML](../../labs/observability/nimbus/oom.yaml)

```bash
kubectl delete -f labs/observability/nimbus/oom.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/oom.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/oom.yaml)

```bash
kubectl delete -f labs/observability/nimbus/oom.yaml --ignore-not-found --wait=true
```
