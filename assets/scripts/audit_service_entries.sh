#!/bin/sh
set -eu
namespace="${1:?Usage: sh assets/scripts/audit_service_entries.sh namespace}"
printf '\nExplicit exportTo wildcard\n'
kubectl get serviceentries.networking.istio.io -n "$namespace" -o go-template='{{range .items}}{{$name := .metadata.name}}{{range .spec.exportTo}}{{if eq . "*"}}{{printf "%s\n" $name}}{{end}}{{end}}{{end}}'
printf '\nMissing or empty exportTo (mesh default applies)\n'
kubectl get serviceentries.networking.istio.io -n "$namespace" -o go-template='{{range .items}}{{if not .spec.exportTo}}{{printf "%s\n" .metadata.name}}{{end}}{{end}}'
printf '\nDuplicate exact TCP VIP:port in this namespace\n'
rows=$(kubectl get serviceentries.networking.istio.io -n "$namespace" -o go-template='{{range .items}}{{$name := .metadata.name}}{{$ports := .spec.ports}}{{range .spec.addresses}}{{$address := .}}{{range $ports}}{{if eq .protocol "TCP"}}{{printf "%s\t%v\t%s\n" $address .number $name}}{{end}}{{end}}{{end}}{{end}}')
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
