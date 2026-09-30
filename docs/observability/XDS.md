# Xds — Nimbus observability labs

## Churn

**Metric:** `pilot_push_triggers`.

**Dashboard:** **Mesh Istio - xDS** → **Push triggers per second**.

**Expected:** Readiness changes every 5 seconds, triggering endpoint updates and xDS pushes.

```bash
kubectl delete -f labs/observability/nimbus/churn.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/churn.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/churn.yaml --ignore-not-found --wait=true
```

## Empty

**Metric:** `pilot_eds_no_instances`.

**Dashboard:** **Mesh Istio - xDS** → **EDS services without instances**.

**Expected:** HTTP 503/UH: the Service has no matching Pods.

```bash
kubectl delete -f labs/observability/nimbus/empty.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/empty.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/empty.yaml --ignore-not-found --wait=true
```

## Unready

**Metric:** `pilot_endpoint_not_ready`.

**Dashboard:** **Mesh Istio - xDS** → **Endpoints not ready**.

**Expected:** The Pod remains unready; requests return HTTP 503/UH.

```bash
kubectl delete -f labs/observability/nimbus/unready.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/unready.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/unready.yaml --ignore-not-found --wait=true
```

## Cds Reject

**Metric:** `envoy_cluster_manager_cds_update_rejected`.

**Dashboard:** **Mesh Istio - Workload** → **CDS updates rejected per interval**.

**Expected:** Envoy rejects the invalid cluster configuration; the CDS rejection counter increases.

```bash
kubectl delete -f labs/observability/nimbus/cds-reject.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/cds-reject.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/cds-reject.yaml --ignore-not-found --wait=true
```

## Excluded

**Metric:** `istio_requests_total`.

**Dashboard:** **Mesh Istio - Workload** → **HTTP rate by status**.

**Expected:** Requests to the excluded service are blocked by REGISTRY_ONLY.

```bash
kubectl delete -f labs/observability/nimbus/excluded.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/excluded.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/excluded.yaml --ignore-not-found --wait=true
```

## Tcp Conflict

**Metric:** `pilot_conflict_outbound_listener_tcp_over_current_tcp`.

**Dashboard:** **Mesh Istio - xDS** → **Outbound listener conflicts**.

**Expected:** The outbound TCP listener conflict metric increases for the duplicated VIP and port.

```bash
kubectl delete -f labs/observability/nimbus/tcp-conflict.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/tcp-conflict.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/tcp-conflict.yaml --ignore-not-found --wait=true
```

## Xds Block

**Metric:** `pilot_xds`.

**Dashboard:** **Mesh Istio - xDS** → **Connected proxies**.

**Expected:** The new proxy cannot connect to Istiod and does not increase the connected-proxy count.

```bash
kubectl delete -f labs/observability/nimbus/xds-block.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/xds-block.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/xds-block.yaml --ignore-not-found --wait=true
```

## Configuration delivery under endpoint churn

**Metric:** `pilot_proxy_convergence_time_bucket`, `pilot_proxy_queue_time_bucket`, `pilot_xds_push_time_bucket`.

**Dashboard:** **Mesh Istio - xDS** → **Proxy convergence p95**, **Proxy queue delay p95**, **Push latency p95**.

**Expected:** Repeated endpoint updates produce samples in convergence, queue-delay and push-latency charts.

```bash
kubectl delete -f labs/observability/nimbus/config-delivery.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/config-delivery.yaml
```

```bash
kubectl delete -f labs/observability/nimbus/config-delivery.yaml --ignore-not-found --wait=true
```
