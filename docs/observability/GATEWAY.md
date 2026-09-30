# Gateway — Nimbus observability labs

All YAML files include namespaces. Run from the repository root with a cluster-admin context; participant RBAC does not allow every resource. Run one scenario at a time. These files are intentionally faulty and must not be added to an auto-sync repository.

Each traffic Job waits 30 seconds, runs 20 workers for 180 seconds, and stops after at most 240 seconds. Native Istio sidecars let Jobs complete. Re-applying a completed Job does not rerun it: the command below deletes only that scenario before recreating it. Never use `kubectl apply -f labs/observability/nimbus/`.

Prometheus scrapes Istiod/Envoy every 15 seconds. Select Last 15 minutes, refresh 15 seconds, and wait 30–60 seconds. Error counters are viewed as rates/increases, not raw totals.

## Gateway Unhealthy

The dedicated obs-gateway receives automatic traffic. The existing gateway-blue stays untouched.

- **Metric:** `envoy_cluster_upstream_cx_none_healthy`.
- **Dashboard:** **Mesh Istio - Gateway** → **No healthy upstream per second**.
- **Filter:** namespace `playground-nimbus-istio-gateway`, Pod `obs-gateway-*`; upstream diagnostics use the `obs-gateway-*.playground-nimbus-istio-enabled.svc.cluster.local` cluster. For Runtime CPU panels select container `istio-proxy`.

**Expected:** Gateway returns 503/UH because subset missing has no endpoints.

[Open complete YAML](../../labs/observability/nimbus/gateway-unhealthy.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-unhealthy.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-unhealthy.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/gateway-unhealthy.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-unhealthy.yaml --ignore-not-found --wait=true
```

## Gateway Tls

The dedicated obs-gateway receives automatic traffic. The existing gateway-blue stays untouched.

- **Metric:** `envoy_cluster_upstream_cx_connect_fail`.
- **Dashboard:** **Mesh Istio - Gateway** → **Connection failures per second**.
- **Filter:** namespace `playground-nimbus-istio-gateway`, Pod `obs-gateway-*`; upstream diagnostics use the `obs-gateway-*.playground-nimbus-istio-enabled.svc.cluster.local` cluster. For Runtime CPU panels select container `istio-proxy`.

**Expected:** Gateway reports a TLS connection failure/503 because SIMPLE TLS targets the HTTP application port. A connect-timeout increase is not required.

[Open complete YAML](../../labs/observability/nimbus/gateway-tls.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-tls.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-tls.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/gateway-tls.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-tls.yaml --ignore-not-found --wait=true
```

## Gateway Overflow

The dedicated obs-gateway receives automatic traffic. The existing gateway-blue stays untouched.

- **Metric:** `envoy_cluster_upstream_rq_pending_overflow`.
- **Dashboard:** **Mesh Istio - Gateway** → **Pending request overflow per second**.
- **Filter:** namespace `playground-nimbus-istio-gateway`, Pod `obs-gateway-*`; upstream diagnostics use the `obs-gateway-*.playground-nimbus-istio-enabled.svc.cluster.local` cluster. For Runtime CPU panels select container `istio-proxy`.

**Expected:** Gateway rejects excess concurrent requests with 503/UO.

[Open complete YAML](../../labs/observability/nimbus/gateway-overflow.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-overflow.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-overflow.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/gateway-overflow.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-overflow.yaml --ignore-not-found --wait=true
```

## Gateway Reject

The dedicated obs-gateway receives automatic traffic. The existing gateway-blue stays untouched.

- **Metric:** `envoy_cluster_manager_cds_update_rejected`.
- **Dashboard:** **Mesh Istio - Gateway** → **CDS updates rejected per interval**.
- **Filter:** namespace `playground-nimbus-istio-gateway`, Pod `obs-gateway-*`; upstream diagnostics use the `obs-gateway-*.playground-nimbus-istio-enabled.svc.cluster.local` cluster. For Runtime CPU panels select container `istio-proxy`.

**Expected:** A CDS rejection counter increases if the invalid field passes admission.

[Open complete YAML](../../labs/observability/nimbus/gateway-reject.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-reject.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-reject.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/gateway-reject.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-reject.yaml --ignore-not-found --wait=true
```

The deliberately invalid Envoy timeout may be rejected by admission in versions that validate it earlier. In that case no CDS NACK reaches Envoy; the admission error is the result. Do not claim the metric changed without checking it.

## Gateway Pressure

The dedicated obs-gateway receives automatic traffic. The existing gateway-blue stays untouched.

- **Metric:** `container_cpu_cfs_throttled_seconds_total`.
- **Dashboard:** **Workload - Runtime** → **Throttled CPU time per second**.
- **Filter:** namespace `playground-nimbus-istio-gateway`, Pod `obs-gateway-*`; upstream diagnostics use the `obs-gateway-*.playground-nimbus-istio-enabled.svc.cluster.local` cluster. For Runtime CPU panels select container `istio-proxy`.

**Expected:** Sustained automatic traffic exercises the dedicated gateway with a 10m CPU limit; inspect throttled time, not just CPU usage.

[Open complete YAML](../../labs/observability/nimbus/gateway-pressure.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-pressure.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-pressure.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/gateway-pressure.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-pressure.yaml --ignore-not-found --wait=true
```

CPU throttling depends on actual load and node scheduling. The manifest requests 10m and limits the dedicated proxy to 10m, with 20 concurrent workers. Do not interpret low CPU usage alone as throttling.

## Gateway Warming

The dedicated obs-gateway receives automatic traffic. The existing gateway-blue stays untouched.

- **Metric:** `envoy_listener_manager_total_listeners_warming`.
- **Dashboard:** **Mesh Istio - Gateway** → **Warming listeners**.
- **Filter:** namespace `playground-nimbus-istio-gateway`, Pod `obs-gateway-*`; upstream diagnostics use the `obs-gateway-*.playground-nimbus-istio-enabled.svc.cluster.local` cluster. For Runtime CPU panels select container `istio-proxy`.

**Expected:** The new 8443 listener waits for the absent obs-missing-cert. HTTP traffic on 8080 continues independently.

[Open complete YAML](../../labs/observability/nimbus/gateway-warming.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-warming.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/gateway-warming.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/gateway-warming.yaml)

```bash
kubectl delete -f labs/observability/nimbus/gateway-warming.yaml --ignore-not-found --wait=true
```
