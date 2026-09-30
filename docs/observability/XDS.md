# Xds — Nimbus observability labs

All YAML files include namespaces. Run from the repository root with a cluster-admin context; participant RBAC does not allow every resource. Run one scenario at a time. These files are intentionally faulty and must not be added to an auto-sync repository.

Each traffic Job waits 30 seconds, runs 20 workers for 180 seconds, and stops after at most 240 seconds. Native Istio sidecars let Jobs complete. Re-applying a completed Job does not rerun it: the command below deletes only that scenario before recreating it. Never use `kubectl apply -f labs/observability/nimbus/`.

Prometheus scrapes Istiod/Envoy every 15 seconds. Select Last 15 minutes, refresh 15 seconds, and wait 30–60 seconds. Error counters are viewed as rates/increases, not raw totals.

## Churn

Apply once; dedicated resources generate the condition and the Job runs traffic automatically.

- **Metric:** `pilot_push_triggers`.
- **Dashboard:** **Mesh Istio - xDS** → **Push triggers per second**.
- **Filter:** Istiod revision `blue`; metric is shared across all workloads served by that revision.

**Expected:** Readiness alternates every 5 seconds, producing EndpointSlice updates and xDS pushes.

[Open complete YAML](../../labs/observability/nimbus/churn.yaml)

```bash
kubectl delete -f labs/observability/nimbus/churn.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/churn.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/churn.yaml)

```bash
kubectl delete -f labs/observability/nimbus/churn.yaml --ignore-not-found --wait=true
```

## Empty

Apply once; dedicated resources generate the condition and the Job runs traffic automatically.

- **Metric:** `pilot_eds_no_instances`.
- **Dashboard:** **Mesh Istio - xDS** → **EDS services without instances**.
- **Filter:** Istiod revision `blue`; metric is shared across all workloads served by that revision.

**Expected:** Requests return 503/UH; the Service has no matching Pods.

[Open complete YAML](../../labs/observability/nimbus/empty.yaml)

```bash
kubectl delete -f labs/observability/nimbus/empty.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/empty.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/empty.yaml)

```bash
kubectl delete -f labs/observability/nimbus/empty.yaml --ignore-not-found --wait=true
```

## Unready

Apply once; dedicated resources generate the condition and the Job runs traffic automatically.

- **Metric:** `pilot_endpoint_not_ready`.
- **Dashboard:** **Mesh Istio - xDS** → **Endpoints not ready**.
- **Filter:** Istiod revision `blue`; metric is shared across all workloads served by that revision.

**Expected:** The backend remains unready and excluded from endpoints; requests return 503/UH.

[Open complete YAML](../../labs/observability/nimbus/unready.yaml)

```bash
kubectl delete -f labs/observability/nimbus/unready.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/unready.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/unready.yaml)

```bash
kubectl delete -f labs/observability/nimbus/unready.yaml --ignore-not-found --wait=true
```

## Cds Reject

Apply once; dedicated resources generate the condition and the Job runs traffic automatically.

- **Metric:** `envoy_cluster_manager_cds_update_rejected`.
- **Dashboard:** **Mesh Istio - Workload** → **CDS updates rejected per interval**.
- **Filter:** namespace `playground-nimbus-istio-enabled`, Pod `obs-cds-reject-traffic-*`; select all upstream clusters, then narrow to `obs-`.

**Expected:** A CDS rejection counter increases if the invalid field passes admission.

[Open complete YAML](../../labs/observability/nimbus/cds-reject.yaml)

```bash
kubectl delete -f labs/observability/nimbus/cds-reject.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/cds-reject.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/cds-reject.yaml)

```bash
kubectl delete -f labs/observability/nimbus/cds-reject.yaml --ignore-not-found --wait=true
```

The deliberately invalid Envoy timeout may be rejected by admission in versions that validate it earlier. In that case no CDS NACK reaches Envoy; the admission error is the result. Do not claim the metric changed without checking it.

## Excluded

Apply once; dedicated resources generate the condition and the Job runs traffic automatically.

- **Metric:** `istio_requests_total`.
- **Dashboard:** **Mesh Istio - Workload** → **HTTP rate by status**.
- **Filter:** namespace `playground-nimbus-istio-enabled`, Pod `obs-excluded-traffic-*`; select all upstream clusters, then narrow to `obs-`.

**Expected:** Traffic is rejected as an unknown destination despite healthy xDS connectivity.

[Open complete YAML](../../labs/observability/nimbus/excluded.yaml)

```bash
kubectl delete -f labs/observability/nimbus/excluded.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/excluded.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/excluded.yaml)

```bash
kubectl delete -f labs/observability/nimbus/excluded.yaml --ignore-not-found --wait=true
```

A 502/503 or connection failure is expected. BlackHole traffic can lack ordinary service labels; use proxy access logs and `istioctl proxy-config clusters` if the HTTP chart has no series.

## Tcp Conflict

Apply once; dedicated resources generate the condition and the Job runs traffic automatically.

- **Metric:** `pilot_conflict_outbound_listener_tcp_over_current_tcp`.
- **Dashboard:** **Mesh Istio - xDS** → **Outbound listener conflicts**.
- **Filter:** Istiod revision `blue`; metric is shared across all workloads served by that revision.

**Expected:** Istiod encounters two services sharing VIP 198.51.100.10:9000; inspect the conflict gauge and proxy listener.

[Open complete YAML](../../labs/observability/nimbus/tcp-conflict.yaml)

```bash
kubectl delete -f labs/observability/nimbus/tcp-conflict.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/tcp-conflict.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/tcp-conflict.yaml)

```bash
kubectl delete -f labs/observability/nimbus/tcp-conflict.yaml --ignore-not-found --wait=true
```

## Xds Block

Apply once; dedicated resources generate the condition and the Job runs traffic automatically.

- **Metric:** `pilot_xds`.
- **Dashboard:** **Mesh Istio - xDS** → **Connected proxies**.
- **Filter:** Istiod revision `blue`; metric is shared across all workloads served by that revision.

**Expected:** The new Job proxy cannot establish xDS; other Nimbus proxies remain unaffected.

[Open complete YAML](../../labs/observability/nimbus/xds-block.yaml)

```bash
kubectl delete -f labs/observability/nimbus/xds-block.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/xds-block.yaml
```

Cleanup before the next scenario:

[Open complete YAML](../../labs/observability/nimbus/xds-block.yaml)

```bash
kubectl delete -f labs/observability/nimbus/xds-block.yaml --ignore-not-found --wait=true
```

The Job proxy starts already blocked from Istiod: expect an unsynced proxy / no new connected-proxy increment, not a guaranteed decrease of the existing cluster-wide count. NetworkPolicy enforcement is required; an additional allow-all policy would override this restriction. Inspect `istioctl proxy-status` as well.

## Configuration delivery under endpoint churn

Ten dedicated Pods alternate readiness every five seconds. This automatically creates repeated endpoint updates and xDS pushes. No shared Istiod resources are patched.

- **Metrics:** `pilot_proxy_convergence_time_bucket`, `pilot_proxy_queue_time_bucket`, `pilot_xds_push_time_bucket`.
- **Dashboard:** **Mesh Istio - xDS** → **Proxy convergence p95**, **Proxy queue delay p95**, **Push latency p95**.
- **Filter:** revision `blue`, all Istiod Pods for that revision.
- **Expected:** new observations in the delivery histograms; slow delivery is not guaranteed on a healthy, lightly loaded control plane.

[Open complete YAML](../../labs/observability/nimbus/config-delivery.yaml)

```bash
kubectl delete -f labs/observability/nimbus/config-delivery.yaml --ignore-not-found --wait=true
kubectl apply -f labs/observability/nimbus/config-delivery.yaml
```

Cleanup:

```bash
kubectl delete -f labs/observability/nimbus/config-delivery.yaml --ignore-not-found --wait=true
```

## Unreachable remote cluster — separate administrator lab

This original example is not included in the Nimbus apply-ready set. Reproducing it requires an isolated Istiod and remote kubeconfig. Adding an invalid remote Secret to shared istio-system would affect the common control plane. `istiod_managed_clusters` alone cannot prove a remote API connection failure; use remote-cluster status and Istiod logs. Do not apply the original broken remote Secret to Karakoram's shared control plane.
