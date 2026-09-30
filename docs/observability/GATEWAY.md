# Mesh Istio - Gateway

Select the gateway Pod and upstream `cluster_name`. TLS passthrough exposes TCP metrics, not HTTP status codes.

## No healthy upstream

`envoy_cluster_upstream_cx_none_healthy`

Increasing rate → check ready endpoints, subset labels and outlier detection. Look for `UH` in access logs.

## Connection or TLS failure

`envoy_cluster_upstream_cx_connect_fail` · `envoy_cluster_upstream_cx_connect_timeout`

Increasing rate → inspect `UF`, transport failure reasons, backend port and TLS/SNI settings. For east-west, check gateway reachability on `15443`.

## Connection pool overflow

`envoy_cluster_upstream_rq_pending_overflow`

Errors under concurrency despite healthy endpoints → check `UO`, `DestinationRule.connectionPool` and backend latency.

## Rejected configuration

`envoy_cluster_manager_cds_update_rejected` · `envoy_listener_manager_lds_update_rejected`

New counter increases after a change → inspect NACK logs and actual Envoy config. Envoy may retain the previous configuration.

## Gateway resources or certificate expiry

`container_cpu_usage_seconds_total` · `container_memory_working_set_bytes` · `kube_pod_container_status_restarts_total` · `envoy_server_days_until_first_cert_expiring`

Rising usage with latency/restarts → check limits, throttling and OOM events. Certificate lifetime approaching zero → check renewal and exact `NotAfter`; zero days need not mean expired.

[Diagnostic commands](../management/ISTIOCTL.md) · [Response flags](https://istio.io/latest/docs/ops/common-problems/network-issues/)
