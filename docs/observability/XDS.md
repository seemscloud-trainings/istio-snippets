# Mesh Istio - xDS

Use the same revision and time range. Counters: `rate()` / `increase()`. Missing data is not zero.

## Disconnected proxies

`pilot_xds`

Unexpected drop across the revision → check `proxy-status`, Istiod restarts and xDS logs. A drop on one replica may be connection redistribution.

## Slow configuration delivery

`pilot_proxy_convergence_time_bucket` · `pilot_proxy_queue_time_bucket` · `pilot_xds_push_time_bucket`

Rising p95 → check Istiod load, queue delay and the affected Envoy config. These measure configuration delivery, not application latency.

## Excessive configuration updates

`pilot_push_triggers` · `pilot_k8s_cfg_events` · `pilot_k8s_reg_events`

Sustained event spikes plus growing queues → inspect endpoint churn, rollouts and repeatedly updated resources. Short rollout spikes are expected.

## Conflicting configuration

`pilot_vservice_dup_domain` · `pilot_conflict_inbound_listener` · `pilot_conflict_outbound_listener_tcp_over_current_tcp`

Persistent nonzero values → check overlapping hosts/ports with `istioctl analyze`, `proxy-config routes` and `listeners`.

## Missing ready endpoints

`pilot_eds_no_instances` · `pilot_endpoint_not_ready`

Services expected to be ready remain empty → check selectors, readiness, EndpointSlices and `proxy-config endpoints`. For remote services, check `remote-clusters`.

[Diagnostic commands](../management/ISTIOCTL.md)
