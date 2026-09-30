# Nimbus fault labs

These checked-in manifests are intentionally faulty, never automatically applied or synced. Namespace fields are explicit. Each scenario owns unique obs-* workloads and a bounded traffic Job. Gateway scenarios share a dedicated obs-gateway and must be cleaned up before another scenario. Do not modify participant app-test, gateway-blue or shared Istiod. Validate YAML, embedded Python and ownership offline; runtime results require an explicitly authorized manual lab execution.
