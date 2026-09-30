# Mesh Istio - Gateway · top 5

Wybierz Pod bramy i docelowy `cluster_name`. Wspólne z Workload metryki opisują tutaj odcinek **gateway → upstream**. Przy TLS passthrough patrz na TCP — brama nie widzi statusów HTTP.

## 1. Brak zdrowego backendu

- **Panel:** No healthy upstream per second — `envoy_cluster_upstream_cx_none_healthy`.
- **Problem:** rośnie tempo błędów, choć sama brama działa. Nie ma zdrowego endpointu dostępnego dla wybranej usługi/subsetu.
- **Potwierdź:** `proxy-config endpoints`, etykiety subsetu, readiness i outlier detection. W access logu szukaj `UH`; nie zakładaj awarii procesu gatewaya.

## 2. Backend istnieje, ale połączenie nie powstaje

- **Panele:** Connection failures per second + Connection timeouts per second — `envoy_cluster_upstream_cx_connect_fail`, `envoy_cluster_upstream_cx_connect_timeout`.
- **Problem:** błędy na etapie zestawiania połączenia. Możliwe: zły port, odrzucenie TCP, trasa sieciowa albo TLS/mTLS; metryki same nie rozróżnią przyczyny.
- **Potwierdź:** flagę `UF` i transport failure reason w logu, port/SNI/TLS w `proxy-config clusters`. Dla east-west sprawdź adres i osiągalność bramy na `15443`.

## 3. Gateway odrzuca requesty przez limit puli

- **Panel:** Pending request overflow per second — `envoy_cluster_upstream_rq_pending_overflow`.
- **Problem:** przy większej równoległości rośnie overflow, mimo dostępnych endpointów. Pula/limity requestów blokują część żądań przed obsługą przez aplikację.
- **Potwierdź:** `UO` w access logu i `DestinationRule.connectionPool`; zestaw limity z czasem odpowiedzi backendu. Samo zwiększenie limitów może przenieść przeciążenie na aplikację.

## 4. Nowa konfiguracja nie została przyjęta

- **Panele:** CDS updates rejected per interval + LDS updates rejected per interval — `envoy_cluster_manager_cds_update_rejected`, `envoy_listener_manager_lds_update_rejected`.
- **Problem:** przyrost odrzuceń po zmianie manifestów; Envoy może zachować poprzednią konfigurację. Warming listeners/clusters utrzymujące się długo wskazują też oczekiwanie na zależności.
- **Potwierdź:** komunikat NACK w logach, `proxy-config` i dostępność certyfikatu SDS. Dodatni historyczny licznik bez nowego przyrostu nie oznacza trwającej awarii.

## 5. Problem samej bramy: zasoby albo certyfikat

- **Panele:** Proxy CPU usage + Proxy working set + Proxy restarts per interval + Certificate lifetime remaining — `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`, `kube_pod_container_status_restarts_total`, `envoy_server_days_until_first_cert_expiring`.
- **Problem:** rosną zasoby/latencja i pojawiają się restarty albo termin certyfikatu zbliża się do zera bez odnowienia.
- **Potwierdź:** limity/throttling, powód restartu/OOM oraz `proxy-config secret` i rzeczywiste `NotAfter`. Sam wzrost RAM nie dowodzi wycieku; wartość dni `0` nie musi oznaczać już wygasłego certyfikatu.

[Komendy diagnostyczne](../management/ISTIOCTL.md) · [Flagi Envoya](https://istio.io/latest/docs/ops/common-problems/network-issues/) · [Znaczenie liczników upstream](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats.html)
