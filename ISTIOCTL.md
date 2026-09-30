#### Namespace + Pod

```bash
export NS="${POD_NAMESPACE%-istio-gateway}-istio-enabled"
export POD=app-test-REPLACE-ME
```

#### Versions · client + Istiod blue

```bash
istioctl version --revision blue
```

#### xDS · connected proxies

```bash
istioctl proxy-status --revision blue
```

#### Full Envoy config · JSON

```bash
istioctl proxy-config all "$POD" -n "$NS" -o json
```

#### Analyze · YAML errors

```bash
istioctl analyze --use-kube=false gateway.yaml virtualservice.yaml
```

#### Gateway collisions · live

```bash
istioctl analyze -n "$NS" --revision blue --remote-contexts workshop \
  --analyzer gateway.ConflictingGatewayAnalyzer
```

#### Listeners · ports + protocols

```bash
istioctl proxy-config listeners "$POD" -n "$NS"
```

#### Routes · hosts + paths + destinations

```bash
istioctl proxy-config routes "$POD" -n "$NS" -o json
```

#### Clusters · upstreams + subsets

```bash
istioctl proxy-config clusters "$POD" -n "$NS"
```

#### Endpoints · IP + port + health

```bash
istioctl proxy-config endpoints "$POD" -n "$NS"
```

#### Certificates · status + expiry

```bash
istioctl proxy-config secret "$POD" -n "$NS"
```

#### Bootstrap · proxy startup config

```bash
istioctl proxy-config bootstrap "$POD" -n "$NS" -o json
```

#### Pod · routes + policies

```bash
istioctl experimental describe pod "$POD" -n "$NS"
```

#### Istiod green · xDS sync

```bash
istioctl proxy-status --revision green
```
