# SmartGrocery web

This Next.js app provides the customer and merchant demo against the FastAPI business API. Set `NEXT_PUBLIC_API_URL` to its browser-accessible origin (default `http://localhost:8000`). The root README contains the complete Docker Compose flow.

From `apps/web`:

```powershell
npm ci
npm run dev
```

Open http://localhost:3000. Check changes with `npm run lint` and `npm run build`. The API runs separately at http://localhost:8000. Demo login credentials and workflow are in the root README.

For repository setup, backend commands and the collaboration workflow, read the [root README](../../README.md).
