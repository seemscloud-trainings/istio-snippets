# Mesh Istio - xDS · top 5

Porównuj tę samą rewizję i przedział czasu. Liczniki oceniaj przez `rate()` / `increase()`, nie po wartości od startu procesu. Brak danych nie oznacza zera.

## 1. Proxy tracą połączenie z Istiod

- **Panel:** Connected proxies — `pilot_xds`.
- **Problem:** nagły spadek bez rolloutów. Spadek na jednej replice i wzrost na drugiej może oznaczać przełączenie połączeń; sprawdź sumę dla rewizji.
- **Potwierdź:** `proxy-status`, restarty Istiod i logi połączeń xDS. Sam spadek nie dowodzi przerwy w ruchu — Envoy może nadal używać ostatniej konfiguracji.

## 2. Zmieniony YAML długo nie działa

- **Panele:** Proxy convergence p95 + Proxy queue delay p95 + Push latency p95 — `pilot_proxy_convergence_time_bucket`, `pilot_proxy_queue_time_bucket`, `pilot_xds_push_time_bucket`.
- **Problem:** czas dostarczenia konfiguracji rośnie względem normalnego poziomu. Rosnąca kolejka wskazuje oczekiwanie; rosnący czas push wskazuje wolniejsze przetwarzanie/dystrybucję.
- **Potwierdź:** obciążenie Istiod i konfigurację konkretnego Envoya. To opóźnienie aktualizacji konfiguracji, nie czas odpowiedzi aplikacji.

## 3. Ciągłe przebudowy konfiguracji

- **Panele:** Push triggers per second + Config events per interval + Registry events per interval — `pilot_push_triggers`, `pilot_k8s_cfg_events`, `pilot_k8s_reg_events`.
- **Problem:** długotrwały wzrost zdarzeń razem ze wzrostem convergence/queue. Typowe przy częstych zmianach endpointów, restartach lub kontrolerze stale zapisującym zasoby.
- **Potwierdź:** etykiety `type` / `event`, historię rolloutów i zmian GitOps. Krótki wzrost podczas wdrożenia jest oczekiwany; to nie liczba requestów aplikacji.

## 4. Konflikt hostów albo listenerów

- **Panele:** Duplicate VirtualService domains + Inbound listener conflicts + Outbound listener conflicts — `pilot_vservice_dup_domain`, `pilot_conflict_inbound_listener`, `pilot_conflict_outbound_listener_tcp_over_current_tcp`.
- **Problem:** dodatnie wartości pojawiają się po zmianie routingu; część konfiguracji może nie zostać uwzględniona zgodnie z zamiarem.
- **Potwierdź:** `istioctl analyze`, powtarzające się hosty/porty oraz rzeczywiste `proxy-config routes` i `listeners`. Sam licznik nie wskazuje winnego manifestu.

## 5. Usługa jest znana, ale nie ma gotowych endpointów

- **Panele:** EDS services without instances + Endpoints not ready — `pilot_eds_no_instances`, `pilot_endpoint_not_ready`.
- **Problem:** wartości utrzymują się mimo oczekiwanych działających replik; proxy może nie mieć dokąd skierować ruchu.
- **Potwierdź:** selector Service, readiness, EndpointSlices i `proxy-config endpoints`. W multicluster sprawdź także `remote-clusters`; świadomie pusta usługa nie oznacza awarii Istiod.

[Komendy diagnostyczne](../management/ISTIOCTL.md)
