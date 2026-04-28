# Bhutan NWFP Digital Marketplace Prototype

This is a static, mobile-first PWA prototype for the proposed Bhutan NWFP Digital Marketplace & Management Platform.

It demonstrates:

- Public product catalogue with search and filters
- Product detail with origin, batch, group, and document metadata
- Seller dashboard actions for inventory, orders, CSV upload, and plans
- Files view for sample downloads and management plan links
- GIS-style origin map with filterable markers
- Cart and manual checkout workflow
- Downloadable sample CSV, GeoJSON, shapefile package, images, and plan links
- Generated marketplace hero image used across the first screen and product cards
- Separate management console at `/prototype/management.html`
- Management console uses `National_NWFP_Groups.csv`
- Management map uses `NWFP Management Groups in Bhutan.jpeg`
- PWA manifest and offline service worker

## Run locally

From this directory:

```powershell
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/prototype/
```

The implementation is intentionally framework-light so the screens can later be moved into Django templates with HTMX partials and backed by PostgreSQL/PostGIS.
