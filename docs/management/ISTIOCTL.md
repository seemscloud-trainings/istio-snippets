## Pod + Envoy

```bash
# Versions · client + Istiod blue
istioctl version --revision blue

# xDS · connected proxies
istioctl proxy-status --revision blue

# Full Envoy config · JSON
istioctl proxy-config all pod-0 -o json -n ns

# Analyze · YAML errors
istioctl analyze --use-kube=false gateway.yaml virtualservice.yaml

# Gateway collisions · live
istioctl analyze --revision blue --remote-contexts workshop --analyzer gateway.ConflictingGatewayAnalyzer -n ns

# Listeners · ports + protocols
istioctl proxy-config listeners pod-0 -n ns

# Routes · hosts + paths + destinations
istioctl proxy-config routes pod-0 -o json -n ns

# Clusters · upstreams + subsets
istioctl proxy-config clusters pod-0 -n ns

# Endpoints · IP + port + health
istioctl proxy-config endpoints pod-0 -n ns

# Certificates · status + expiry
istioctl proxy-config secret pod-0 -n ns

# Bootstrap · proxy startup config
istioctl proxy-config bootstrap pod-0 -o json -n ns

# Pod · routes + policies
istioctl experimental describe pod pod-0 -n ns

# Istiod green · xDS sync
istioctl proxy-status --revision green
```

## Istiod + mesh

```bash
# xDS · detailed status per resource type
istioctl proxy-status --revision blue --verbosity 1
istioctl proxy-status --revision green --verbosity 1

# Istiod replicas · sent vs acknowledged xDS
istioctl experimental internal-debug syncz --revision blue --all

# Istiod · last config push
istioctl experimental internal-debug push_status --revision blue --all

# Service registry · services known to Istiod
istioctl experimental internal-debug registryz --revision blue

# Discovery · endpoints known to Istiod
istioctl experimental internal-debug endpointz --revision blue

# Injection · selected webhook and revision
istioctl experimental check-inject deployment/app-test -n ns

# Revision tags · tag → control plane
istioctl tag list

# Authorization · policies loaded into Envoy
istioctl experimental authz check pod-0 -n ns

# Upstream failures · timeouts, retries, connection errors
istioctl experimental envoy-stats pod-0 --type clusters -n ns

# Envoy counters · Prometheus format
istioctl experimental envoy-stats pod-0 -o prom -n ns
```

## East-west + multicluster

```bash
# Remote discovery · connected clusters and sync state
istioctl remote-clusters --revision blue
istioctl remote-clusters --revision green

# Mesh networks · east-west gateway addresses
istioctl experimental internal-debug networkz --revision blue

# Source proxy · cluster ID, network and locality
istioctl proxy-config bootstrap pod-0 -o json -n ns

# Upstream · TLS transport and service configuration
istioctl proxy-config clusters pod-0 --fqdn app-test.ns.svc.cluster.local --port 80 -o json -n ns

# Service endpoints · local Pods and remote gateway IPs
istioctl proxy-config endpoints pod-0 --cluster "outbound|80||app-test.ns.svc.cluster.local" -o json -n ns

# Different networks · remote gateway endpoints on 15443
istioctl proxy-config endpoints pod-0 --port 15443 -n ns

# Unhealthy endpoints · rejected upstreams
istioctl proxy-config endpoints pod-0 --status unhealthy -n ns

# Two Pods in one cluster · matching root CA
istioctl proxy-config rootca-compare pod-0.ns pod-1.ns
```

## Admin kubeconfig · cluster checks

```bash
# Multicluster · discovery from both clusters
istioctl --context cluster-1 remote-clusters --revision blue
istioctl --context cluster-2 remote-clusters --revision blue

# East-west listener · SNI and TLS on 15443
istioctl --context cluster-1 proxy-config listeners gateway-eastwest-0 --port 15443 -o json -n istio-gateway-system

# East-west upstreams · SNI-based service clusters
istioctl --context cluster-1 proxy-config clusters gateway-eastwest-0 -o json -n istio-gateway-system

# East-west certificates · validity and trust chain
istioctl --context cluster-1 proxy-config secret gateway-eastwest-0 -n istio-gateway-system

# Entire cluster · invalid and conflicting configuration
istioctl --context cluster-1 analyze --all-namespaces --revision blue
istioctl --context cluster-1 analyze --all-namespaces --revision green

# Multicluster analysis · both contexts
istioctl --context cluster-1 analyze --all-namespaces --revision blue --remote-contexts cluster-2

# TLS Secrets · references and certificates
istioctl --context cluster-1 analyze --all-namespaces --revision blue --remote-contexts cluster-1 --analyzer gateway.SecretAnalyzer --analyzer gateway.CertificateAnalyzer
```

## Upgrade · istioctl from the target release

```bash
# Precheck · cluster prerequisites
istioctl --context cluster-1 experimental precheck

# Upgrade 1.29 → 1.30 · compatibility changes
istioctl --context cluster-1 experimental precheck --from-version 1.29

# Installed versions · old and new control plane
istioctl --context cluster-1 version --revision blue
istioctl --context cluster-1 version --revision green

# Injection versions · namespace vs running Pods
istioctl --context cluster-1 experimental injector list

# Canary control plane · connected proxies after migration
istioctl --context cluster-1 proxy-status --revision blue --verbosity 1
istioctl --context cluster-1 proxy-status --revision green --verbosity 1
```
