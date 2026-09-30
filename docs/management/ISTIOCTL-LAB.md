# istioctl - Lab

## Contexts · administrator terminal

Use your administrator kubeconfig with both contexts. The participant `istioctl` Pod is scoped to that participant; use the Nimbus section below from its Headlamp terminal.

```bash
K=gke_prod-common-apps_europe-west1_karakoram
H=gke_prod-common-apps_europe-west1_himalaya

# Verify the available cluster contexts
kubectl config get-contexts "$K" "$H"
```

## Control planes · versions and revisions

```bash
# Karakoram: installed versions and connected proxies
istioctl --context "$K" version --revision blue
istioctl --context "$K" version --revision green
istioctl --context "$K" proxy-status --revision blue
istioctl --context "$K" proxy-status --revision green

# Himalaya: installed versions and connected proxies
istioctl --context "$H" version --revision blue
istioctl --context "$H" version --revision green
istioctl --context "$H" proxy-status --revision blue
istioctl --context "$H" proxy-status --revision green

# Istiod replicas and actual images
kubectl --context "$K" -n istio-system get deployments istiod-blue istiod-green -o wide
kubectl --context "$H" -n istio-system get deployments istiod-blue istiod-green -o wide

# Namespace injection labels and revision tags
kubectl --context "$K" get namespaces -L istio.io/rev,istio-injection,topology.istio.io/network
kubectl --context "$H" get namespaces -L istio.io/rev,istio-injection,topology.istio.io/network
istioctl --context "$K" tag list
istioctl --context "$H" tag list
```

## Multicluster · remote discovery

`remote-clusters` lists Kubernetes clusters known to Istiod. `proxy-config clusters` lists Envoy upstream destinations.

```bash
# Remote API synchronization, checked in both directions and both revisions
istioctl --context "$K" remote-clusters --revision blue
istioctl --context "$K" remote-clusters --revision green
istioctl --context "$H" remote-clusters --revision blue
istioctl --context "$H" remote-clusters --revision green

# Remote Secret names only; do not print kubeconfig tokens
kubectl --context "$K" -n istio-system get secrets -l 'istio/multiCluster=true'
kubectl --context "$H" -n istio-system get secrets -l 'istio/multiCluster=true'

# Networks and discovered east-west gateways
istioctl --context "$K" experimental internal-debug networkz --revision green
istioctl --context "$H" experimental internal-debug networkz --revision green

# Registry and endpoints known to each control plane
istioctl --context "$K" experimental internal-debug registryz --revision green
istioctl --context "$H" experimental internal-debug registryz --revision green
istioctl --context "$K" experimental internal-debug endpointz --revision green
istioctl --context "$H" experimental internal-debug endpointz --revision green
```

## Gateways · workloads, addresses and declared listeners

Observed east-west VIPs: Karakoram `10.100.152.250`, Himalaya `10.110.2.250`. Use the Service output for current addresses.

```bash
# Public, internal and east-west gateway Deployments and Services
kubectl --context "$K" -n istio-gateway-system get deployments,services -o wide
kubectl --context "$H" -n istio-gateway-system get deployments,services -o wide

# Istio Gateway resources across namespaces
kubectl --context "$K" get gateways.networking.istio.io -A
kubectl --context "$H" get gateways.networking.istio.io -A

# Full declared listeners, selectors and TLS modes
kubectl --context "$K" get gateways.networking.istio.io -A -o yaml
kubectl --context "$H" get gateways.networking.istio.io -A -o yaml
```

## East-west proxies · active listeners and upstreams

Port `15443` carries cross-network service traffic. AUTO_PASSTHROUGH routes using SNI; HTTP route output is not the primary check for this listener.

```bash
# SNI filter chains and TLS on both east-west gateways
istioctl --context "$K" proxy-config listeners deployment/gateway-eastwest -n istio-gateway-system --port 15443 -o json
istioctl --context "$H" proxy-config listeners deployment/gateway-eastwest -n istio-gateway-system --port 15443 -o json

# Upstream service clusters
istioctl --context "$K" proxy-config clusters deployment/gateway-eastwest -n istio-gateway-system
istioctl --context "$H" proxy-config clusters deployment/gateway-eastwest -n istio-gateway-system

# Certificate validity and active SDS secrets
istioctl --context "$K" proxy-config secret deployment/gateway-eastwest -n istio-gateway-system
istioctl --context "$H" proxy-config secret deployment/gateway-eastwest -n istio-gateway-system

# Bootstrap: cluster ID, network, node metadata and discovery address
istioctl --context "$K" proxy-config bootstrap deployment/gateway-eastwest -n istio-gateway-system -o json
istioctl --context "$H" proxy-config bootstrap deployment/gateway-eastwest -n istio-gateway-system -o json
```

## Shared nginx · declared routing

Both clusters expose `nginx.prod-example.svc.cluster.local`. The VirtualService has `/karakoram` and `/himalaya` routes to named subsets.

```bash
# Kubernetes endpoints and Pod placement
kubectl --context "$K" -n prod-example get pods,services,endpointslices -o wide
kubectl --context "$H" -n prod-example get pods,services,endpointslices -o wide

# VirtualService, subsets and gateway binding
kubectl --context "$K" -n prod-example get virtualservice nginx -o yaml
kubectl --context "$K" -n prod-example get destinationrule nginx -o yaml
kubectl --context "$K" -n prod-example get gateway prod-example -o yaml
kubectl --context "$H" -n prod-example get virtualservice nginx -o yaml
kubectl --context "$H" -n prod-example get destinationrule nginx -o yaml
```

## Shared nginx · configuration actually loaded in Envoy

Cross-network endpoints should include the opposite east-west VIP on `15443`; same-network endpoints use Pod addresses. A Kubernetes EndpointSlice alone does not show the proxy's complete cross-cluster view.

```bash
# Listeners and HTTP routes on the application sidecars
istioctl --context "$K" proxy-config listeners deployment/nginx -n prod-example
istioctl --context "$K" proxy-config routes deployment/nginx -n prod-example -o json
istioctl --context "$H" proxy-config routes deployment/nginx -n prod-example -o json

# Service clusters, subsets and outbound TLS configuration
istioctl --context "$K" proxy-config clusters deployment/nginx -n prod-example --fqdn nginx.prod-example.svc.cluster.local -o json
istioctl --context "$H" proxy-config clusters deployment/nginx -n prod-example --fqdn nginx.prod-example.svc.cluster.local -o json

# Combined service endpoints
istioctl --context "$K" proxy-config endpoints deployment/nginx -n prod-example --cluster 'outbound|80||nginx.prod-example.svc.cluster.local'
istioctl --context "$H" proxy-config endpoints deployment/nginx -n prod-example --cluster 'outbound|80||nginx.prod-example.svc.cluster.local'

# Explicit remote subsets
istioctl --context "$K" proxy-config endpoints deployment/nginx -n prod-example --cluster 'outbound|80|himalaya|nginx.prod-example.svc.cluster.local'
istioctl --context "$H" proxy-config endpoints deployment/nginx -n prod-example --cluster 'outbound|80|karakoram|nginx.prod-example.svc.cluster.local'

# All destinations routed through a remote east-west gateway
istioctl --context "$K" proxy-config endpoints deployment/nginx -n prod-example --port 15443
istioctl --context "$H" proxy-config endpoints deployment/nginx -n prod-example --port 15443
```

## Shared nginx · request reaches the other cluster

These GETs generate traffic. Compare the response identifying each destination with the route selected above.

```bash
# Karakoram client: local and remote destinations
kubectl --context "$K" -n prod-example exec deployment/nginx -c nginx -- wget -qO- http://nginx.prod-example.svc.cluster.local/karakoram
kubectl --context "$K" -n prod-example exec deployment/nginx -c nginx -- wget -qO- http://nginx.prod-example.svc.cluster.local/himalaya

# Himalaya client: local and remote destinations
kubectl --context "$H" -n prod-example exec deployment/nginx -c nginx -- wget -qO- http://nginx.prod-example.svc.cluster.local/himalaya
kubectl --context "$H" -n prod-example exec deployment/nginx -c nginx -- wget -qO- http://nginx.prod-example.svc.cluster.local/karakoram
```

## MongoDB · remote member routing and TLS

This inspects the mesh transport, not MongoDB replica-set health. Query `rs.status()` separately for PRIMARY/SECONDARY state and replication lag.

```bash
# Database Pods and operator status
kubectl --context "$K" -n prod-example get psmdb,pods
kubectl --context "$H" -n prod-example get psmdb,pods

# Karakoram → individual Himalaya members
istioctl --context "$K" proxy-config clusters mdb-karakoram-rs0-0 -n prod-example --fqdn mdb-himalaya-rs0-0.prod-example.svc.cluster.local -o json
istioctl --context "$K" proxy-config endpoints mdb-karakoram-rs0-0 -n prod-example --cluster 'outbound|27017||mdb-himalaya-rs0-0.prod-example.svc.cluster.local'
istioctl --context "$K" proxy-config endpoints mdb-karakoram-rs0-0 -n prod-example --cluster 'outbound|27017||mdb-himalaya-rs0-1.prod-example.svc.cluster.local'

# Himalaya → individual Karakoram members
istioctl --context "$H" proxy-config endpoints mdb-himalaya-rs0-0 -n prod-example --cluster 'outbound|27017||mdb-karakoram-rs0-0.prod-example.svc.cluster.local'

# Workload certificates and mesh policies
istioctl --context "$K" proxy-config secret mdb-karakoram-rs0-0 -n prod-example
istioctl --context "$H" proxy-config secret mdb-himalaya-rs0-0 -n prod-example
kubectl --context "$K" -n prod-example get peerauthentication,authorizationpolicy,destinationrule -o yaml
kubectl --context "$H" -n prod-example get peerauthentication,authorizationpolicy,destinationrule -o yaml
```

## Nimbus · Headlamp terminal in the Nimbus istioctl Pod

Open `istioctl` in `playground-nimbus-istio-gateway`. These commands use the Pod's ServiceAccount and local kubeconfig; no administrator context variables are needed. Do not target another participant's namespace.

```bash
# Own application sidecar: listeners, routes and upstreams
istioctl proxy-config listeners deployment/app-test -n playground-nimbus-istio-enabled
istioctl proxy-config routes deployment/app-test -n playground-nimbus-istio-enabled -o json
istioctl proxy-config clusters deployment/app-test -n playground-nimbus-istio-enabled
istioctl proxy-config endpoints deployment/app-test -n playground-nimbus-istio-enabled
istioctl proxy-config secret deployment/app-test -n playground-nimbus-istio-enabled

# Own blue gateway: real HTTP routes and TLS listeners
istioctl proxy-config listeners deployment/gateway-blue -n playground-nimbus-istio-gateway
istioctl proxy-config routes deployment/gateway-blue -n playground-nimbus-istio-gateway -o json
istioctl proxy-config clusters deployment/gateway-blue -n playground-nimbus-istio-gateway
istioctl proxy-config secret deployment/gateway-blue -n playground-nimbus-istio-gateway

# Own green gateway: compare loaded listeners/routes
istioctl proxy-config listeners deployment/gateway-green -n playground-nimbus-istio-gateway
istioctl proxy-config routes deployment/gateway-green -n playground-nimbus-istio-gateway -o json
```

## Diagnosis · rejected configuration, logs and policy

```bash
# Cluster-wide analysis for both revisions
istioctl --context "$K" analyze --all-namespaces --revision blue
istioctl --context "$K" analyze --all-namespaces --revision green
istioctl --context "$H" analyze --all-namespaces --revision green

# Analyze both connected clusters together
istioctl --context "$K" analyze --all-namespaces --revision green --remote-contexts "$H"

# Namespace-scoped mesh configuration
kubectl --context "$K" -n prod-example get sidecar,serviceentry,virtualservice,destinationrule,peerauthentication,authorizationpolicy,telemetry -o yaml

# Control-plane errors and remote synchronization events
kubectl --context "$K" -n istio-system logs deployment/istiod-green --since=10m --tail=200
kubectl --context "$H" -n istio-system logs deployment/istiod-green --since=10m --tail=200

# East-west proxy connection/TLS errors
kubectl --context "$K" -n istio-gateway-system logs deployment/gateway-eastwest -c istio-proxy --since=10m --tail=200
kubectl --context "$H" -n istio-gateway-system logs deployment/gateway-eastwest -c istio-proxy --since=10m --tail=200
```
