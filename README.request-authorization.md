#### Validate JWT when present

```yaml
# Apply one request-authorization example at a time; no other matching policies.
# Existing shop/api (app=api) returns 200. Replace issuer/JWKS with your IdP.
# $VALID: signed, unexpired JWT with this issuer and audience; $INVALID: bad signature.
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: api-jwt
  namespace: shop
spec:
  selector:
    matchLabels:
      app: api
  jwtRules:
    - issuer: https://issuer.example.test/
      audiences: [shop-api]
      jwksUri: https://issuer.example.test/.well-known/jwks.json
```

![Validate JWT when present](images/request-authorization/validate-only.png)

#### Require a valid JWT

```yaml
# Alternative to validate-only.yaml; existing shop/api returns 200 /orders.
# Replace issuer/JWKS with your IdP; $VALID matches issuer/audience and is unexpired.
# $INVALID has an invalid signature.
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: api-jwt
  namespace: shop
spec:
  selector:
    matchLabels:
      app: api
  jwtRules:
    - issuer: https://issuer.example.test/
      audiences: [shop-api]
      jwksUri: https://issuer.example.test/.well-known/jwks.json
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: api-jwt-access
  namespace: shop
spec:
  selector:
    matchLabels:
      app: api
  action: ALLOW
  rules:
    - from:
        - source:
            requestPrincipals: ["*"]
```

![Require a valid JWT](images/request-authorization/require-token.png)

#### Public health check + JWT role for orders

```yaml
# Alternative example; existing shop/api returns 200 /orders and /healthz.
# Replace issuer/JWKS; valid $ADMIN has role=admin, valid $USER has role=user.
# /healthz permits missing JWT; an invalid supplied JWT is still rejected.
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: api-jwt
  namespace: shop
spec:
  selector:
    matchLabels:
      app: api
  jwtRules:
    - issuer: https://issuer.example.test/
      audiences: [shop-api]
      jwksUri: https://issuer.example.test/.well-known/jwks.json
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: api-jwt-access
  namespace: shop
spec:
  selector:
    matchLabels:
      app: api
  action: ALLOW
  rules:
    - to:
        - operation:
            methods: [GET]
            paths: [/healthz]
    - from:
        - source:
            requestPrincipals: ["*"]
      to:
        - operation:
            methods: [GET]
            paths: [/orders]
      when:
        - key: request.auth.claims[role]
          values: [admin]
```

![Public health check + JWT role for orders](images/request-authorization/admin-and-health.png)
