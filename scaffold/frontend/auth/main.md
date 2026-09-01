# Auth — Layer 2

> Parent: [../main.md](../main.md)
> Last audited: 2026-08-31 @ commit dc6c386

## Purpose
Handles user authentication: Azure AD SSO (primary), legacy username/password login, JWT token management, and auth state propagation via React Context.

## Tech stack & conventions
- `@azure/msal-browser` ^5.0.2 + `@azure/msal-react` ^5.0.2 for Azure AD
- JWT tokens stored in `localStorage`, attached to axios via interceptor
- Auth state managed through React Context (`AuthContext`)
- Two roles: `administrador`, `tecnico`

## Structure
```
auth/
├── authConfig.ts          # MSAL configuration (client ID, tenant, scopes)
├── AuthContext.tsx         # React Context: user, token, login, logout, isAdmin
├── Login.tsx              # Login form (Azure SSO button + legacy username/password)
└── AzureCallback.tsx      # Azure AD redirect handler (extracts token, calls backend)
```

## Entry points
- `authConfig.ts`: exports `msalConfig` and `loginRequest` objects
- `AuthContext.tsx`: exports `AuthProvider` wrapper and `useAuth()` hook
- `Login.tsx`: rendered when `!isAuthenticated` in App.tsx
- `AzureCallback.tsx`: route `/azure-callback`

## Key interactions
- **Frontend -> Backend:** `POST /api/auth/azure-login` with Azure ID token -> receives local JWT + user object
- **Frontend -> Backend:** `POST /api/auth/login` with username/password -> receives local JWT + user object
- **Frontend -> Backend:** `GET /api/auth/me` with Bearer token -> returns current user profile
- **Token lifecycle:** localStorage persistence, axios interceptor auto-attaches Bearer header
- **Session expiry:** 401/403 responses trigger logout via axios interceptor in AuthContext

## Common tasks & gotchas
- To add a new auth provider: create config in `authConfig.ts`, add login method in `AuthContext.tsx`, add button in `Login.tsx`
- Azure tenant/client IDs are hardcoded as fallbacks in `authConfig.ts` — env vars `VITE_AZURE_CLIENT_ID` and `VITE_AZURE_TENANT_ID` override them
- `loginWithAzure` sends the Azure ID token (not access token) to the backend — the backend validates it via JWKS
- `isInitialLoad` flag prevents re-fetching user on token restore (only on first mount)

## Open questions / TODO
- The `@supabase/supabase-js` dependency is imported in package.json but usage is unclear — may be dead
- No token refresh logic — tokens expire after 24h and user must re-login
- No role-based route protection (isAdmin check is UI-only, not enforced in routing)
