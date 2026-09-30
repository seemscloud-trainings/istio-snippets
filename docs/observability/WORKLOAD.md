# Mesh Istio - Workload · top 5

Wybierz aplikację, docelowy `cluster_name` i jeden reporter. Metryki upstream na sidecarze klienta opisują **aplikacja → zależność**; na proxy serwera mogą opisywać **Envoy → lokalny kontener**. Sprawdzaj kierunek klastra.

## 1. Retry ukrywają awarię zależności

- **Panele:** Upstream retries per second + Retry limit exceeded per second — `envoy_cluster_upstream_rq_retry`, `envoy_cluster_upstream_rq_retry_limit_exceeded`.
- **Problem:** klient nadal dostaje `200`, ale rośnie liczba prób i opóźnienie. Po wyczerpaniu liczby dozwolonych prób rośnie drugi licznik.
- **Potwierdź:** `VirtualService.retries`, błędy zależności i liczbę prób w trace/logach. `503 → 503 → 200` to dwie dodatkowe próby, mimo końcowego sukcesu.

## 2. Timeout odpowiedzi czy problem z połączeniem?

- **Panele:** Upstream timeouts per second + Connection timeouts per second — `envoy_cluster_upstream_rq_timeout`, `envoy_cluster_upstream_cx_connect_timeout`.
- **Problem:** rośnie `rq_timeout` — upłynął czas oczekiwania na odpowiedź; rośnie `cx_connect_timeout` — timeout zestawiania połączenia. To różne etapy requestu.
- **Potwierdź:** `timeout` / `perTryTimeout`, logi transportu i czas pracy zależności. Sprawdź też opóźnienie w puli; sam timeout requestu nie dowodzi wolnego kodu aplikacji.

## 3. Circuit breaker odcina nadmiar równoległych żądań

- **Panel:** Pending request overflow per second — `envoy_cluster_upstream_rq_pending_overflow`.
- **Problem:** błędy rosną dopiero przy większej równoległości, czasem przy niskim CPU. Proxy osiąga limit puli/requestów; wolny backend długo zajmuje dostępne miejsca.
- **Potwierdź:** `UO`, `maxConnections`, `http1MaxPendingRequests`, `http2MaxRequests` i opóźnienie zależności. Sprawdź ustawienia na proxy wysyłającym ruch, nie tylko na serwerze.

## 4. Zależność resetuje requesty

- **Panel:** Request resets received per second — `envoy_cluster_upstream_rq_rx_reset`.
- **Problem:** upstream przerywa request zamiast zwrócić pełną odpowiedź. Często koreluje z restartem, rolloutem, zamykaniem połączeń lub błędem protokołu.
- **Potwierdź:** logi obu proxy, restarty backendu i jego graceful shutdown. Nie każdy reset jest crashem aplikacji — odróżnij restart od normalnego zamykania połączeń.

## 5. Przeciążona aplikacja czy jej Envoy?

- **Panele:** Application CPU usage / working set / restarts oraz Proxy CPU usage / working set / restarts — `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`, `kube_pod_container_status_restarts_total`, `kube_pod_init_container_status_restarts_total`.
- **Problem:** zasoby i restarty rosną po stronie aplikacji albo tylko `istio-proxy`. Suma dla całego Poda ukrywa tę różnicę; native sidecar ma restart counter w metrykach init-containerów.
- **Potwierdź:** konkretny kontener, OOM/throttling, limity i moment wzrostu latencji. Wysokie CPU bez błędów i opóźnień samo w sobie nie oznacza awarii.

[Komendy diagnostyczne](../management/ISTIOCTL.md) · [Znaczenie liczników upstream](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats.html)
