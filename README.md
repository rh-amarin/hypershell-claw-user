# hypershell-claw-user

Exploration log of a real-user simulation of the [openshift-online/hypershell](https://github.com/openshift-online/hypershell) platform and its OpenShell gateways, run by **Lemon** — an OpenClaw agent operating from inside an OpenShell sandbox on the hyp2 cluster.

## 🌐 Live site

**View the full exploration journal at: https://rh-amarin.github.io/hypershell-claw-user/**

- **[Overview](https://rh-amarin.github.io/hypershell-claw-user/)** — latest run summary and stats
- **[Run log](https://rh-amarin.github.io/hypershell-claw-user/log.html)** — one entry per test execution
- **[Test catalog](https://rh-amarin.github.io/hypershell-claw-user/catalog.html)** — every unique test case with all-time pass rates

The site regenerates automatically after each test battery and is pushed by the agent itself.

## What's in here

- `index.html`, `log.html`, `catalog.html` — generated exploration-log site (source copies; the Pages build serves `docs/`)
- `docs/` — the same site, served by GitHub Pages
- `gen-site.py` — site generator, run over the structured `test-results*.json` files
- `tools-gen-site.py` — alias of the generator

## Method

Every test runs against a real OpenShell gateway via its gRPC API (hand-encoded protobuf over gRPC-web, no CLI required) with a gateway service account. Sandboxes, providers, templates, lifecycle operations, and fleet statistics are exercised end-to-end; every created resource is deleted and verified gone afterwards.
