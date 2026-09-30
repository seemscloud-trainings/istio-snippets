#### Gateway + VirtualService + DestinationRule

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: debug-duplicate-certificate
spec:
  selector:
    istio: gateway-nimbus-blue
  servers:
  - port:
      number: 443
      name: https-debug
      protocol: HTTPS
    hosts: [debug.wp.pl]
    tls:
      mode: SIMPLE
      credentialName: istio-gateway-wildcard
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: debug-missing-gateway
spec:
  hosts: [debug.wp.pl]
  gateways: [debug-gateway-does-not-exist]
  exportTo: [.]
  http:
  - route:
    - destination:
        host: debug-backend.wp.pl
        port:
          number: 443
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: debug-tls-without-ca
spec:
  host: debug-backend.wp.pl
  exportTo: [.]
  trafficPolicy:
    tls:
      mode: SIMPLE
```

#### Apply · Nimbus enabled

```bash
kubectl apply -f assets/observability/debug-routing.yaml -n playground-nimbus-istio-enabled
```

#### Analyze

```bash
istioctl analyze --revision blue --failure-threshold Warning -n playground-nimbus-istio-enabled
```

#### Verified diagnostics

```text
Error   IST0101  VirtualService/debug-missing-gateway: gateway not found
Warning IST0128  DestinationRule/debug-tls-without-ca: SIMPLE without caCertificates
Warning IST0138  Gateway/debug-duplicate-certificate: certificate shared by gateways
```

#### Cleanup

```bash
kubectl delete -f assets/observability/debug-routing.yaml -n playground-nimbus-istio-enabled
```
