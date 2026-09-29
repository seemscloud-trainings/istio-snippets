#### STRICT + ServiceAccount

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: api-mtls
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: api-access
spec:
  action: ALLOW
  rules: [{from: [{source: {principals: [cluster.local/ns/shop/sa/reader]}}], to: [{operation: {methods: [GET], paths: [/orders]}}]}]
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: api-plaintext-client
spec:
  host: api.shop.svc.cluster.local
  exportTo: [.]
  trafficPolicy:
    tls:
      mode: DISABLE
```

![STRICT + ServiceAccount](images/peer-authorization/strict-reader.png)

#### PERMISSIVE + ServiceAccount

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: api-mtls
spec:
  mtls:
    mode: PERMISSIVE
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: api-access
spec:
  action: ALLOW
  rules: [{from: [{source: {principals: [cluster.local/ns/shop/sa/reader]}}], to: [{operation: {methods: [GET], paths: [/orders]}}]}]
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: api-plaintext-client
spec:
  host: api.shop.svc.cluster.local
  exportTo: [.]
  trafficPolicy:
    tls:
      mode: DISABLE
```

![PERMISSIVE + ServiceAccount](images/peer-authorization/permissive-identity.png)

#### DENY + ALLOW

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: api-mtls
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: api-access
spec:
  action: ALLOW
  rules: [{from: [{source: {principals: [cluster.local/ns/shop/sa/reader]}}], to: [{operation: {methods: [GET, POST], paths: [/orders, /admin]}}]}]
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: api-deny-admin-write
spec:
  action: DENY
  rules: [{to: [{operation: {ports: ['8080'], methods: [POST], paths: [/admin]}}]}]
```

![DENY + ALLOW](images/peer-authorization/deny-admin-write.png)
