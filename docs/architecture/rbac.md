# SmartGrocery RBAC

This document defines authentication and authorization for FastAPI.
It matches the roles in `docs/architecture/erd.md`.

## 1. Roles

| Role | Who | Default after register |
|---|---|---|
| `customer` | B2C shopper | yes |
| `merchant` | Store operator using `/dashboard` | no, seeded or assigned |
| `admin` | Technical/store owner, same merchant APIs plus user management | no, seeded |

A user has exactly one role in MVP.

## 2. Authentication

- Register and login issue a JWT access token and a refresh token.
- Access token TTL: 15 minutes.
- Refresh token TTL: 7 days, stored hashed in the database (table can be added in the auth implementation PR).
- Password hashing: Argon2 or bcrypt.
- `Authorization: Bearer <access_token>` on protected routes.
- Inactive users (`is_active = false`) cannot authenticate.

## 3. Permission matrix

| Action | customer | merchant | admin |
|---|---|---|---|
| Register / login / refresh | yes | yes | yes |
| Read public catalog | yes | yes | yes |
| Read product detail | yes | yes | yes |
| Checkout and create order | own | no | no |
| Read own orders | yes | yes | yes |
| Read all store orders | no | yes | yes |
| Update order status (fulfil/cancel) | no | yes | yes |
| Read inventory positions and batches | no | yes | yes |
| Adjust / quarantine batch | no | yes | yes |
| CRUD suppliers | no | yes | yes |
| Create / approve / receive purchase orders | no | yes | yes |
| Read forecasts and recommendations | no | yes | yes |
| Approve / reject recommendation | no | yes | yes |
| Trigger forecast job | no | yes | yes |
| Manage users and roles | no | no | yes |
| Change business rule parameters | no | no | yes |

Merchant cannot call customer checkout on behalf of a shopper in MVP.

## 4. Route guards

| Prefix | Guard |
|---|---|
| `/api/v1/auth/register`, `/login`, `/refresh` | public |
| `/api/v1/products` GET, `/api/v1/categories` GET | public |
| `/api/v1/orders` | authenticated; customers scoped to `customer_id = me` |
| `/api/v1/inventory`, `/suppliers`, `/purchase-orders`, `/forecasts`, `/recommendations`, `/jobs` | `merchant` or `admin` |
| `/api/v1/admin` | `admin` |

## 5. Error codes

| HTTP | When |
|---|---|
| 401 | missing/invalid/expired token |
| 403 | authenticated but role cannot perform the action |
| 404 | resource missing, or customer tries to read someone else's order (do not leak existence) |
