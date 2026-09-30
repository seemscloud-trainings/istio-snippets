# istioctl - Lab

Run commands inside the `istioctl` Pod of the cluster being inspected. Shared-resource commands require the corresponding RBAC permissions. For the opposite direction, open the Pod on the other cluster.

## Control planes · versions and revisions

```bash
# Current cluster: installed versions and connected proxies
istioctl version --revision blue
istioctl version --revision green
istioctl proxy-status --revision blue
istioctl proxy-status --revision green


# Istiod replicas and actual images
kubectl -n istio-system get deployments istiod-blue istiod-green -o wide

# Namespace injection labels and revision tags
kubectl get namespaces -L istio.io/rev,istio-injection,topology.istio.io/network
istioctl tag list
```

## Multicluster · remote discovery

`remote-clusters` lists Kubernetes clusters known to Istiod. `proxy-config clusters` lists Envoy upstream destinations.

```bash
# Remote API synchronization, checked in both directions and both revisions
istioctl remote-clusters --revision blue
istioctl remote-clusters --revision green

# Remote Secret names only; do not print kubeconfig tokens
kubectl -n istio-system get secrets -l 'istio/multiCluster=true'

# Networks and discovered east-west gateways
istioctl experimental internal-debug networkz --revision green

# Registry and endpoints known to each control plane
istioctl experimental internal-debug registryz --revision green
istioctl experimental internal-debug endpointz --revision green
```

## Gateways · workloads, addresses and declared listeners

Observed east-west VIPs: Karakoram `10.100.152.250`, Himalaya `10.110.2.250`. Use the Service output for current addresses.

```bash
# Public, internal and east-west gateway Deployments and Services
kubectl -n istio-gateway-system get deployments,services -o wide

# Istio Gateway resources across namespaces
kubectl get gateways.networking.istio.io -A

# Full declared listeners, selectors and TLS modes
kubectl get gateways.networking.istio.io -A -o yaml
```

## East-west proxies · active listeners and upstreams

Port `15443` carries cross-network service traffic. AUTO_PASSTHROUGH routes using SNI; HTTP route output is not the primary check for this listener.

```bash
# SNI filter chains and TLS on both east-west gateways
istioctl proxy-config listeners deployment/gateway-eastwest -n istio-gateway-system --port 15443 -o json

# Upstream service clusters
istioctl proxy-config clusters deployment/gateway-eastwest -n istio-gateway-system

# Certificate validity and active SDS secrets
istioctl proxy-config secret deployment/gateway-eastwest -n istio-gateway-system

# Bootstrap: cluster ID, network, node metadata and discovery address
istioctl proxy-config bootstrap deployment/gateway-eastwest -n istio-gateway-system -o json
```

## Shared nginx · declared routing

Both clusters expose `nginx.prod-example.svc.cluster.local`. The VirtualService has `/karakoram` and `/himalaya` routes to named subsets.

```bash
# Kubernetes endpoints and Pod placement
kubectl -n prod-example get pods,services,endpointslices -o wide

# VirtualService, subsets and gateway binding
kubectl -n prod-example get virtualservice nginx -o yaml
kubectl -n prod-example get destinationrule nginx -o yaml
kubectl -n prod-example get gateway prod-example -o yaml
```

## Shared nginx · configuration actually loaded in Envoy

Cross-network endpoints should include the opposite east-west VIP on `15443`; same-network endpoints use Pod addresses. A Kubernetes EndpointSlice alone does not show the proxy's complete cross-cluster view.

```bash
# Listeners and HTTP routes on the application sidecars
istioctl proxy-config listeners deployment/nginx -n prod-example
istioctl proxy-config routes deployment/nginx -n prod-example -o json

# Service clusters, subsets and outbound TLS configuration
istioctl proxy-config clusters deployment/nginx -n prod-example --fqdn nginx.prod-example.svc.cluster.local -o json

# Combined service endpoints
istioctl proxy-config endpoints deployment/nginx -n prod-example --cluster 'outbound|80||nginx.prod-example.svc.cluster.local'

# Destination subsets: inspect both; the other cluster uses its east-west VIP
istioctl proxy-config endpoints deployment/nginx -n prod-example --cluster 'outbound|80|himalaya|nginx.prod-example.svc.cluster.local'
istioctl proxy-config endpoints deployment/nginx -n prod-example --cluster 'outbound|80|karakoram|nginx.prod-example.svc.cluster.local'

# All destinations routed through a remote east-west gateway
istioctl proxy-config endpoints deployment/nginx -n prod-example --port 15443
```

## Shared nginx · request reaches the other cluster

These GETs generate traffic. Compare the response identifying each destination with the route selected above.

```bash
# Current cluster: explicit Karakoram and Himalaya destinations
kubectl -n prod-example exec deployment/nginx -c nginx -- wget -qO- http://nginx.prod-example.svc.cluster.local/karakoram
kubectl -n prod-example exec deployment/nginx -c nginx -- wget -qO- http://nginx.prod-example.svc.cluster.local/himalaya
```

## MongoDB · remote member routing and TLS

This inspects the mesh transport, not MongoDB replica-set health. Query `rs.status()` separately for PRIMARY/SECONDARY state and replication lag.

```bash
# Database Pods and operator status
kubectl -n prod-example get psmdb,pods

# From the Karakoram istioctl Pod → individual Himalaya members
istioctl proxy-config clusters mdb-karakoram-rs0-0 -n prod-example --fqdn mdb-himalaya-rs0-0.prod-example.svc.cluster.local -o json
istioctl proxy-config endpoints mdb-karakoram-rs0-0 -n prod-example --cluster 'outbound|27017||mdb-himalaya-rs0-0.prod-example.svc.cluster.local'
istioctl proxy-config endpoints mdb-karakoram-rs0-0 -n prod-example --cluster 'outbound|27017||mdb-himalaya-rs0-1.prod-example.svc.cluster.local'

# From the Himalaya istioctl Pod → individual Karakoram members
istioctl proxy-config endpoints mdb-himalaya-rs0-0 -n prod-example --cluster 'outbound|27017||mdb-karakoram-rs0-0.prod-example.svc.cluster.local'

# Certificates: run the matching Pod command on its own cluster; policies are local
istioctl proxy-config secret mdb-karakoram-rs0-0 -n prod-example
istioctl proxy-config secret mdb-himalaya-rs0-0 -n prod-example
kubectl -n prod-example get peerauthentication,authorizationpolicy,destinationrule -o yaml
```

## Nimbus · Headlamp terminal in the Nimbus istioctl Pod

Open `istioctl` in `playground-nimbus-istio-gateway`. These commands use the Pod's ServiceAccount and local kubeconfig; no context flags are needed. Do not target another participant's namespace.

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
istioctl analyze --all-namespaces --revision blue
istioctl analyze --all-namespaces --revision green

# Namespace-scoped mesh configuration
kubectl -n prod-example get sidecar,serviceentry,virtualservice,destinationrule,peerauthentication,authorizationpolicy,telemetry -o yaml

# Control-plane errors and remote synchronization events
kubectl -n istio-system logs deployment/istiod-green --since=10m --tail=200

# East-west proxy connection/TLS errors
kubectl -n istio-gateway-system logs deployment/gateway-eastwest -c istio-proxy --since=10m --tail=200
```
