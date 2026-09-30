# Nimbus fault labs

These checked-in manifests are intentionally faulty, never automatically applied or synced. Namespace fields are explicit. Each scenario owns unique obs-* workloads and a bounded traffic Job. Each gateway scenario owns a separate gateway, Service, selector and host so all scenarios can run together. run-all.sh deletes only labeled lab Jobs and applies the explicit Kustomization resource list; it never passes Markdown files to kubectl. Do not modify participant app-test, gateway-blue or shared Istiod. Validate YAML, embedded Python and ownership offline; runtime results require an explicitly authorized manual lab execution.

CDS rejection Jobs wait for an initial scrape, then PATCH only their named EnvoyFilter using a dedicated ServiceAccount and namespace Role. Reset detection uses upstream_cx_destroy_remote_with_active_rq for TCP resets. The xDS-disconnected Job uses an unreachable discoveryAddress as well as NetworkPolicy, making the disconnect independent of CNI policy enforcement.

The missing-certificate gateway explicitly disables the initial SDS fetch timeout only on its 8443 filter chain so the listener remains warming instead of activating after the default timeout. The HTTP listener remains independently usable.
