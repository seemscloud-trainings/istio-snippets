# Istio snippets

This repository contains workshop documentation, YAML examples and supporting images. Component documentation lives in docs/components; image links resolve relative to each Markdown file. Preserve existing examples and image assets when adding explanations.

Keep examples concise and explain matching separately from destination selection. ServiceEntry addresses are service IP/VIP matches, endpoints are backend destinations, and resolution controls how those destinations are selected. Scope IP-only explanations to TCP; HTTP Host and TLS SNI can affect matching. REGISTRY_ONLY handles unknown destinations and is not a complete outbound security boundary. Validate Markdown links, YAML syntax and the scoped diff without applying workshop examples to a cluster.

Observability exercises use labs/observability/nimbus/*.yaml and explicit Nimbus namespaces. Keep automatic traffic bounded, fault resources isolated and cleanup explicit. Never apply those manifests while editing documentation. Validate metric/panel mappings against provisioned dashboard JSON; document version-dependent rejection behavior and control-plane scenarios that cannot be guaranteed by apply alone.
