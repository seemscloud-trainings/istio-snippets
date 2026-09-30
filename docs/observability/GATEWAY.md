## No healthy upstream

`envoy_cluster_upstream_cx_none_healthy`

Replace the lab gateway route; no backend Pod matches the subset. Requests for wp.pl produce UH/503 even though other subsets may be healthy.

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: fault-lab
spec:
  host: app-test.ns.svc.cluster.local
  exportTo: [.]
  subsets:
  - name: missing
    labels:
      version: does-not-exist
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: fault-lab
spec:
  hosts: [wp.pl]
  gateways: [gateway-blue]
  exportTo: [.]
  http:
  - route:
    - destination:
        host: app-test.ns.svc.cluster.local
        port:
          number: 80
        subset: missing
```

## TLS sent to a plaintext backend

`envoy_cluster_upstream_cx_connect_fail` · `envoy_cluster_upstream_cx_connect_timeout`

Gateway namespace; the existing route targets app-test.ns:80, which serves plaintext HTTP. SIMPLE forces TLS to that port. Send requests and inspect UF and transport failure reasons.

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: fault-lab
spec:
  host: app-test.ns.svc.cluster.local
  exportTo: [.]
  trafficPolicy:
    tls:
      mode: SIMPLE
      sni: wp.pl
```

## Connection pool overflow

`envoy_cluster_upstream_rq_pending_overflow`

Gateway namespace; backend app-test.ns:80 must take about 3 seconds. Send at least 20 concurrent requests through the gateway → UO/overflow. Sequential requests may succeed.

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: fault-lab
spec:
  host: app-test.ns.svc.cluster.local
  exportTo: [.]
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 1
      http:
        http1MaxPendingRequests: 1
        http2MaxRequests: 1
        h2UpgradePolicy: DO_NOT_UPGRADE
```

## Rejected configuration

`envoy_cluster_manager_cds_update_rejected`

Gateway namespace; app-test.ns:80 must already be routed. This deliberately invalid Envoy timeout triggers CDS rejection; the previous valid configuration may remain active.

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: bad-connect-timeout
spec:
  configPatches:
  - applyTo: CLUSTER
    match:
      context: GATEWAY
      cluster:
        service: app-test.ns.svc.cluster.local
        portNumber: 80
    patch:
      operation: MERGE
      value:
        connect_timeout: -1s
```

## Gateway CPU or memory pressure

`container_cpu_usage_seconds_total` · `container_memory_working_set_bytes` · `kube_pod_container_status_restarts_total`

Apply as a strategic merge patch to the lab gateway. Under load, very small limits can cause throttling or OOM/restarts. Confirm termination reasons; CPU usage alone is not proof.

**Deployment patch · existing gateway-blue**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway-blue
spec:
  template:
    spec:
      containers:
      - name: istio-proxy
        resources:
          requests:
            cpu: 10m
            memory: 16Mi
          limits:
            cpu: 10m
            memory: 16Mi
```
