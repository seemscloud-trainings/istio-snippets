#### Duplicate TCP VIP + exportTo wildcard

```yaml
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: debug-tcp-one
spec:
  hosts: [one.wp.pl]
  addresses: [198.51.100.42]
  exportTo: ['*']
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
  name: debug-tcp-two
spec:
  hosts: [two.wp.pl]
  addresses: [198.51.100.42]
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

#### Apply · disposable namespace

```bash
kubectl apply -f assets/service-entry/conflict-export.yaml -n ns
```

#### Audit · namespace-local configuration

```bash
printf '\nExplicit exportTo wildcard\n'
kubectl get serviceentries.networking.istio.io -n ns -o go-template='{{range .items}}{{$name := .metadata.name}}{{range .spec.exportTo}}{{if eq . "*"}}{{printf "%s\n" $name}}{{end}}{{end}}{{end}}'
printf '\nMissing or empty exportTo (mesh default applies)\n'
kubectl get serviceentries.networking.istio.io -n ns -o go-template='{{range .items}}{{if not .spec.exportTo}}{{printf "%s\n" .metadata.name}}{{end}}{{end}}'
printf '\nDuplicate exact TCP VIP:port in this namespace\n'
rows=$(kubectl get serviceentries.networking.istio.io -n ns -o go-template='{{range .items}}{{$name := .metadata.name}}{{$ports := .spec.ports}}{{range .spec.addresses}}{{$address := .}}{{range $ports}}{{if eq .protocol "TCP"}}{{printf "%s\t%v\t%s\n" $address .number $name}}{{end}}{{end}}{{end}}{{end}}')
printf '%s\n' "$rows" | awk -F '\t' '
  NF == 3 {
    key = $1 ":" $2
    count[key]++
    names[key] = names[key] " " $3
  }
  END {
    for (key in count)
      if (count[key] > 1) print key " ->" names[key]
  }
'
```

```text
Explicit exportTo wildcard
debug-tcp-one

Missing or empty exportTo (mesh default applies)

Duplicate exact TCP VIP:port in this namespace
198.51.100.42:9000 -> debug-tcp-one debug-tcp-two
```

`exportTo: ["*"]` is valid Istio configuration; `analyze` does not reject it. The duplicate check covers identical explicit TCP addresses/ports in one namespace, not every possible routing conflict.

#### Envoy · generated listener

```bash
istioctl proxy-config listeners pod-0 --address 198.51.100.42 --port 9000 -o json -n ns
```

#### Istiod · conflict metric

`pilot_conflict_outbound_listener_tcp_over_current_tcp` — inspect the revision serving the affected proxy. The entries must be visible to that proxy; an existing Sidecar may exclude them.

#### Cleanup

```bash
kubectl delete -f assets/service-entry/conflict-export.yaml -n ns
```
