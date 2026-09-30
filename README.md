# Components

- [Service Entry](docs/components/SERVICE-ENTRY.md)
- [VirtualService](docs/components/VIRTUAL-SERVICE.md)
- [Gateway + VirtualService](docs/components/GATEWAY.md)
- [Sidecar](docs/components/SIDECAR.md)
- [ProxyConfig](docs/components/PROXY-CONFIG.md)
- [Telemetry](docs/components/TELEMETRY.md)
- [WorkloadGroup + WorkloadEntry](docs/components/VM-WORKLOADS.md)
- [AuthorizationPolicy + PeerAuthentication](docs/components/PEER-AUTHORIZATION.md)
- [RequestAuthentication + AuthorizationPolicy](docs/components/REQUEST-AUTHORIZATION.md)

# Configurations

- [Gateway gRPC](docs/configurations/GATEWAY-GRPC.md)
- [CronJob](docs/configurations/CRONJOB.md)

- [Analyze errors](docs/configurations/ANALYZE-ERRORS.md)
- [ServiceEntry conflicts + exports](docs/configurations/SERVICE-ENTRY-CONFLICTS.md)

# Management

- [istioctl](docs/management/ISTIOCTL.md)
- [istioctl - Lab](docs/management/ISTIOCTL-LAB.md)

# Observability

- [xDS](docs/observability/XDS.md)
- [Gateway](docs/observability/GATEWAY.md)
- [Workload](docs/observability/WORKLOAD.md)

Nimbus observability labs: the [xDS](docs/observability/XDS.md), [Gateway](docs/observability/GATEWAY.md) and [Workload](docs/observability/WORKLOAD.md) guides link complete manifests under `labs/observability/nimbus/`. Each includes namespaces and an automatic bounded traffic Job. Run one at a time and use its cleanup command. Shared-control-plane disruptions are explicitly excluded from participant apply-ready manifests.
