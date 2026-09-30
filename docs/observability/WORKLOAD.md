# Mesh Istio - Workload

Select one reporter and upstream `cluster_name`. Client-side metrics describe application → dependency; server-side upstreams may describe Envoy → local container.

## Retries hide failures

`envoy_cluster_upstream_rq_retry` · `envoy_cluster_upstream_rq_retry_limit_exceeded`

Retries and latency rise despite final `200` responses → check retry settings and dependency errors. `503 → 503 → 200` still means two retries.

## Response timeout vs connection timeout

`envoy_cluster_upstream_rq_timeout` · `envoy_cluster_upstream_cx_connect_timeout`

`rq_timeout`: response deadline exceeded. `cx_connect_timeout`: connection setup timed out. Check route deadlines, pool delay and dependency latency.

## Circuit breaker rejects requests

`envoy_cluster_upstream_rq_pending_overflow`

Failures appear under concurrency → check `UO`, connection/request limits and slow dependencies on the sending proxy.

## Upstream resets requests

`envoy_cluster_upstream_rq_rx_reset`

Increasing resets → correlate upstream logs with restarts, rollouts, shutdown and protocol errors. A reset alone does not prove an application crash.

## Application or Envoy overload

`container_cpu_usage_seconds_total` · `container_memory_working_set_bytes` · `kube_pod_container_status_restarts_total` · `kube_pod_init_container_status_restarts_total`

Compare application containers with `istio-proxy`. Correlate latency with throttling, OOM or restarts; native sidecar restarts use init-container metrics.

[Diagnostic commands](../management/ISTIOCTL.md) · [Upstream counters](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats.html)
