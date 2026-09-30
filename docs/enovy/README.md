# LDS — listenery i porty
istioctl proxy-config listeners pod-0 -n ns

# RDS — routing HTTP
istioctl proxy-config routes pod-0 -o json -n ns

# CDS — upstreamy, TLS i connection pool
istioctl proxy-config clusters pod-0 -o json -n ns

# EDS — IP, porty i stan backendów
istioctl proxy-config endpoints pod-0 -n ns

# SDS — certyfikaty i ich ważność
istioctl proxy-config secret pod-0 -n ns

# Połączenia i status xDS
istioctl proxy-status --revision blue --verbosity 1
