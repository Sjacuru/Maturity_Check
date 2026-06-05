# Frontend deployment model — FastAPI serves Vue dist

Phase 1 deployment model: FastAPI serves the compiled Vue application as static files. The frontend is not treated as an independently deployed subsystem. Vite remains a development tool only.

During development, the Vite dev server runs on port 5173 with a proxy to FastAPI on port 8000. This is a development convenience, not an architectural ownership decision — it does not affect the production model or introduce CORS configuration into the production path.

**Why:** One deployment artifact, one URL, one operational process. Simpler current operation and simpler future rollout to a workplace network or internet exposure without architectural restructuring. Choosing the "closer to definitive" option is also the simpler option here.

**Considered alternative:** Standalone Vue deployment (independent server/process). Rejected because it introduces production CORS concerns, splits the operational model, and adds deployment complexity with no benefit for a solo academic tool with one Auditor.
