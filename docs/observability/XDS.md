## Disconnected proxies

`pilot_xds`

Client namespace; NetworkPolicy enforcement required, with no other policy allowing port 15012. On reconnect, app-test cannot reach Istiod; existing connections may survive until closed.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-xds
spec:
  podSelector:
    matchLabels:
      app: app-test
  policyTypes: [Egress]
  egress:
  - ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 8080
```

## Slow configuration delivery

`pilot_proxy_convergence_time_bucket` · `pilot_proxy_queue_time_bucket` · `pilot_xds_push_time_bucket`

Low Istiod CPU limits can grow queues and convergence time under load. Change lab configuration while generating traffic; idle Istiod may show no slowdown.

**Istiod chart values · isolated control plane**

```yaml
resources:
  requests:
    cpu: 10m
  limits:
    cpu: 10m
```

## Endpoint churn

`pilot_k8s_reg_events` · `pilot_push_triggers`

Readiness flips every five seconds → endpoint updates and repeated pushes. This creates configuration churn without restarting the application.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churn-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: churn-lab
  template:
    metadata:
      labels:
        app: churn-lab
        sidecar.istio.io/inject: 'true'
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: busybox:1.37.0
        command: [httpd, -f, -p, '8080']
        readinessProbe:
          exec:
            command: [sh, -c, test $(( $(date +%s) / 5 % 2 )) -eq 0]
          periodSeconds: 1
          successThreshold: 1
          failureThreshold: 1
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: [ALL]
---
apiVersion: v1
kind: Service
metadata:
  name: churn-lab
spec:
  selector:
    app: churn-lab
  ports:
  - name: http
    port: 80
    targetPort: 8080
```

## Conflicting TCP listeners

`pilot_conflict_outbound_listener_tcp_over_current_tcp`

Two TCP services claim the same VIP:9000. Inspect the conflict counter and generated listener; both destinations cannot be distinguished on that address.

```yaml
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: one
spec:
  hosts: [one.wp.pl]
  addresses: [198.51.100.10]
  exportTo: [.]
  location: MESH_EXTERNAL
  resolution: STATIC
  ports:
  - number: 9000
    name: tcp
    protocol: TCP
  endpoints:
  - address: 192.0.2.10
---
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: two
spec:
  hosts: [two.wp.pl]
  addresses: [198.51.100.10]
  exportTo: [.]
  location: MESH_EXTERNAL
  resolution: STATIC
  ports:
  - number: 9000
    name: tcp
    protocol: TCP
  endpoints:
  - address: 192.0.2.20
```

## Service without endpoints

`pilot_eds_no_instances`

No Pod has app=does-not-exist. The service has no endpoints; inspect EDS and the selector.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: empty-lab
spec:
  selector:
    app: does-not-exist
  ports:
  - name: http
    port: 80
    targetPort: 8080
```

## Pods never become ready

`pilot_endpoint_not_ready` · `pilot_eds_no_instances`

The process runs but its readiness probe always fails. EndpointSlices contain an unready endpoint; it is excluded from normal routing.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unready-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: unready-lab
  template:
    metadata:
      labels:
        app: unready-lab
        sidecar.istio.io/inject: 'true'
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: busybox:1.37.0
        command: [httpd, -f, -p, '8080']
        readinessProbe:
          exec:
            command: [sh, -c, exit 1]
          periodSeconds: 2
          failureThreshold: 1
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: [ALL]
---
apiVersion: v1
kind: Service
metadata:
  name: unready-lab
spec:
  selector:
    app: unready-lab
  ports:
  - name: http
    port: 80
    targetPort: 8080
```

## Envoy rejects a cluster

`envoy_cluster_manager_cds_update_rejected`

Client namespace; app-test.ns must exist. The negative connect timeout is deliberately invalid for Envoy. Expect a CDS NACK; inspect the proxy counter in Gateway/Workload and Istiod logs.

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: bad-connect-timeout
spec:
  configPatches:
  - applyTo: CLUSTER
    match:
      context: SIDECAR_OUTBOUND
      cluster:
        service: app-test.ns.svc.cluster.local
        portNumber: 80
    patch:
      operation: MERGE
      value:
        connect_timeout: -1s
```

## Gateway waits for an absent TLS Secret

`envoy_listener_manager_total_listeners_warming`

Use the gateway namespace. missing-lab-cert must not exist; replace the lab listener/route. A new HTTPS listener waits for SDS. An existing listener may keep its previous certificate.

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: gateway-blue
spec:
  selector:
    istio: gateway-blue
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts: [wp.pl]
    tls:
      mode: SIMPLE
      credentialName: missing-lab-cert
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
```

## Sidecar excludes a dependency



Client namespace; replace its existing Sidecar. app-test.ns is excluded. With REGISTRY_ONLY, requests to it are blocked; xDS may remain fully synced.

```yaml
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: default
spec:
  egress:
  - hosts: [istio-system/*]
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY
```

## Remote cluster cannot be synchronized

`istiod_managed_clusters`

Isolated istio-system namespace. The remote API address refuses connections. Check remote-clusters and Istiod logs; managed-cluster count alone does not prove connectivity.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: istio-remote-secret-remote-lab
  labels:
    istio/multiCluster: 'true'
  annotations:
    networking.istio.io/cluster: remote-lab
type: Opaque
stringData:
  remote-lab: |
    apiVersion: v1
    kind: Config
    clusters:
    - name: remote-lab
      cluster:
        server: https://127.0.0.1:1
    users:
    - name: remote-lab
      user:
        token: invalid-lab-token
    contexts:
    - name: remote-lab
      context:
        cluster: remote-lab
        user: remote-lab
    current-context: remote-lab
```
