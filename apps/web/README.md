# SmartGrocery web

This Next.js app currently provides a storefront and merchant dashboard **visual shell**. The products and categories use `lib/mock-data.ts`; login, cart, checkout and several dashboard pages are not wired to the FastAPI backend. See [release readiness #46](https://github.com/ztdayyyyyyyyyy2112/smartgrocery/issues/46) for the remaining integration work.

From `apps/web`:

```powershell
npm ci
npm run dev
```

Open http://localhost:3000. Check changes with `npm run lint` and `npm run build`. The API runs separately at http://localhost:8000; `NEXT_PUBLIC_API_URL` is reserved for the upcoming integration.

For repository setup, backend commands and the collaboration workflow, read the [root README](../../README.md).
