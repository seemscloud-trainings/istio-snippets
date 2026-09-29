#### Local namespace

```yaml
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: client-egress
  namespace: shop
spec:
  workloadSelector:
    labels:
      app: client
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY
  egress: [{hosts: [./*, istio-system/*]}]
```

![Local namespace](images/sidecar/local-only.png)

#### One remote service

```yaml
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: client-egress
  namespace: shop
spec:
  workloadSelector:
    labels:
      app: client
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY
  egress: [{hosts: [./*, istio-system/*, payments/api.payments.svc.cluster.local]}]
```

![One remote service](images/sidecar/import-service.png)

#### ALLOW_ANY

```yaml
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: client-egress
  namespace: shop
spec:
  workloadSelector:
    labels:
      app: client
  outboundTrafficPolicy:
    mode: ALLOW_ANY
  egress: [{hosts: [./*, istio-system/*]}]
```

![ALLOW_ANY](images/sidecar/allow-any.png)
