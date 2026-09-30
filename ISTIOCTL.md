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

## Istiod + mesh

#### xDS · detailed status per resource type

```bash
istioctl proxy-status --revision blue --verbosity 1
istioctl proxy-status --revision green --verbosity 1
```

#### Istiod replicas · sent vs acknowledged xDS

```bash
istioctl experimental internal-debug syncz --revision blue --all
```

#### Istiod · last config push

```bash
istioctl experimental internal-debug push_status --revision blue --all
```

#### Service registry · services known to Istiod

```bash
istioctl experimental internal-debug registryz --revision blue
```

#### Discovery · endpoints known to Istiod

```bash
istioctl experimental internal-debug endpointz --revision blue
```

#### Injection · selected webhook and revision

```bash
istioctl experimental check-inject deployment/app-test -n "$NS"
```

#### Revision tags · tag → control plane

```bash
istioctl tag list
```

#### Authorization · policies loaded into Envoy

```bash
istioctl experimental authz check "$POD" -n "$NS"
```

#### Upstream failures · timeouts, retries, connection errors

```bash
istioctl experimental envoy-stats "$POD" -n "$NS" --type clusters
```

#### Envoy counters · Prometheus format

```bash
istioctl experimental envoy-stats "$POD" -n "$NS" -o prom
```

## East-west + multicluster

#### Remote discovery · connected clusters and sync state

```bash
istioctl remote-clusters --revision blue
istioctl remote-clusters --revision green
```

#### Mesh networks · east-west gateway addresses

```bash
istioctl experimental internal-debug networkz --revision blue
```

#### Source proxy · cluster ID, network and locality

```bash
istioctl proxy-config bootstrap "$POD" -n "$NS" -o json
```

#### Destination service

```bash
export SERVICE="app-test.${NS}.svc.cluster.local"
export SERVICE_PORT=80
```

#### Upstream · TLS transport and service configuration

```bash
istioctl proxy-config clusters "$POD" -n "$NS" \
  --fqdn "$SERVICE" --port "$SERVICE_PORT" -o json
```

#### Service endpoints · local Pods and remote gateway IPs

```bash
istioctl proxy-config endpoints "$POD" -n "$NS" \
  --cluster "outbound|${SERVICE_PORT}||${SERVICE}" -o json
```

#### Different networks · remote gateway endpoints on 15443

```bash
istioctl proxy-config endpoints "$POD" -n "$NS" --port 15443
```

#### Unhealthy endpoints · rejected upstreams

```bash
istioctl proxy-config endpoints "$POD" -n "$NS" --status unhealthy
```

#### Two Pods in one cluster · matching root CA

```bash
export PEER_POD=REPLACE-WITH-PEER-POD
export PEER_NS="$NS"
istioctl proxy-config rootca-compare "$POD.$NS" "$PEER_POD.$PEER_NS"
```

## Admin kubeconfig · cluster checks

#### Admin context + east-west Pod

```bash
export KUBECONFIG=/path/to/admin-kubeconfig
export CTX_A=gke_prod-common-apps_europe-west1_karakoram
export CTX_B=gke_prod-common-apps_europe-west1_himalaya
export EASTWEST_NS=istio-system
export EASTWEST_POD=REPLACE-WITH-EASTWEST-POD
```

#### Multicluster · discovery from both clusters

```bash
istioctl --context "$CTX_A" remote-clusters --revision blue
istioctl --context "$CTX_B" remote-clusters --revision blue
```

#### East-west listener · SNI and TLS on 15443

```bash
istioctl --context "$CTX_A" proxy-config listeners "$EASTWEST_POD" \
  -n "$EASTWEST_NS" --port 15443 -o json
```

#### East-west upstreams · SNI-based service clusters

```bash
istioctl --context "$CTX_A" proxy-config clusters "$EASTWEST_POD" \
  -n "$EASTWEST_NS" -o json
```

#### East-west certificates · validity and trust chain

```bash
istioctl --context "$CTX_A" proxy-config secret "$EASTWEST_POD" \
  -n "$EASTWEST_NS"
```

#### Entire cluster · invalid and conflicting configuration

```bash
istioctl --context "$CTX_A" analyze --all-namespaces --revision blue
istioctl --context "$CTX_A" analyze --all-namespaces --revision green
```

#### Multicluster analysis · both contexts

```bash
istioctl --context "$CTX_A" analyze --all-namespaces \
  --revision blue --remote-contexts "$CTX_B"
```

## Upgrade · istioctl from the target release

#### Precheck · cluster prerequisites

```bash
istioctl --context "$CTX_A" experimental precheck
```

#### Upgrade 1.29 → 1.30 · compatibility changes

```bash
istioctl --context "$CTX_A" experimental precheck --from-version 1.29
```

#### Installed versions · old and new control plane

```bash
istioctl --context "$CTX_A" version --revision blue
istioctl --context "$CTX_A" version --revision green
```

#### Injection versions · namespace vs running Pods

```bash
istioctl --context "$CTX_A" experimental injector list
```

#### Canary control plane · connected proxies after migration

```bash
istioctl --context "$CTX_A" proxy-status --revision blue --verbosity 1
istioctl --context "$CTX_A" proxy-status --revision green --verbosity 1
```
