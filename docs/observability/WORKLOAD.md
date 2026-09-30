## Retries hide failures

`envoy_cluster_upstream_rq_retry` · `envoy_cluster_upstream_rq_retry_limit_exceeded`

Replace the lab route. Trouble /test/cosmos-retry must return a mix of 200/503. Repeated requests produce retries and sometimes a final 200; an always-200 backend will not reproduce this.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: fault-lab
spec:
  hosts: [playground-trouble.prod-playground-trouble.svc.cluster.local]
  gateways: [mesh]
  exportTo: [.]
  http:
  - route:
    - destination:
        host: playground-trouble.prod-playground-trouble.svc.cluster.local
        port:
          number: 80
    retries:
      attempts: 2
      perTryTimeout: 1s
      retryOn: 5xx
    timeout: 5s
```

## Response deadline is too short

`envoy_cluster_upstream_rq_timeout`

Replace the lab route. Trouble /test/cosmos-timeout takes 3 seconds; the client proxy stops waiting after 100 ms. Send a request → response timeout, commonly 504.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: fault-lab
spec:
  hosts: [playground-trouble.prod-playground-trouble.svc.cluster.local]
  gateways: [mesh]
  exportTo: [.]
  http:
  - route:
    - destination:
        host: playground-trouble.prod-playground-trouble.svc.cluster.local
        port:
          number: 80
    retries:
      attempts: 0
    timeout: 100ms
```

## Circuit breaker rejects concurrent requests

`envoy_cluster_upstream_rq_pending_overflow`

Client namespace. Trouble /test/cosmos-connections takes 3 seconds. Use this route and send at least 20 concurrent requests; the small pool rejects excess requests.

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: fault-lab
spec:
  host: playground-trouble.prod-playground-trouble.svc.cluster.local
  exportTo: [.]
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 1
      http:
        http1MaxPendingRequests: 1
        http2MaxRequests: 1
        h2UpgradePolicy: DO_NOT_UPGRADE
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: fault-lab
spec:
  hosts: [playground-trouble.prod-playground-trouble.svc.cluster.local]
  gateways: [mesh]
  exportTo: [.]
  http:
  - route:
    - destination:
        host: playground-trouble.prod-playground-trouble.svc.cluster.local
        port:
          number: 80
    retries:
      attempts: 0
    timeout: 10s
```

## Application resets upstream requests

`envoy_cluster_upstream_rq_rx_reset`

Send HTTP requests to reset-lab:80. The application resets its TCP socket. Inspect the destination sidecar inbound cluster and reset logs; the client sidecar may only see the resulting 503.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reset-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: reset-lab
  template:
    metadata:
      labels:
        app: reset-lab
        sidecar.istio.io/inject: 'true'
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: python:3.12-alpine
        command: [python, -u, -c]
        args:
        - |
          import socket, socketserver, struct
          class Reset(socketserver.BaseRequestHandler):
              def handle(self):
                  self.request.recv(4096)
                  self.request.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                  self.request.close()
          socketserver.TCPServer.allow_reuse_address = True
          socketserver.TCPServer(("0.0.0.0", 8080), Reset).serve_forever()
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: [ALL]
---
apiVersion: v1
kind: Service
metadata:
  name: reset-lab
spec:
  selector:
    app: reset-lab
  ports:
  - name: http
    port: 80
    targetPort: 8080
```

## Application or Envoy overload

`container_cpu_usage_seconds_total` · `container_memory_working_set_bytes` · `kube_pod_container_status_restarts_total` · `kube_pod_init_container_status_restarts_total`

Strategic merge patch for an existing app-test Deployment with container api. Small application limits isolate application pressure; proxy limits remain unchanged. Check api OOM/throttling separately from istio-proxy.

**Deployment patch · existing api container**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-test
spec:
  template:
    spec:
      containers:
      - name: api
        resources:
          requests:
            cpu: 10m
            memory: 8Mi
          limits:
            cpu: 10m
            memory: 8Mi
```
