# Bhutan NWFP Platform — Execution Plan

## Status
- [x] Vision defined
- [x] Data assets collected (shapefiles, GeoPackage, PDFs, prototype)
- [ ] Phase 1 MVP in progress

## Project Root
```
nwfp_platform/     ← Django project (this directory)
prototype/         ← Static prototype (reference only)
NWFP Groups Shp Files/
nwfp_groups_gpkeg_files/
management_plans_nwfp/
data_csv/
```

## Quick Start (after scaffold)
```bash
cd nwfp_platform
cp .env.example .env          # fill in values
docker-compose up -d db       # start PostGIS
pip install -r requirements/development.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Phase 1 — MVP (current)

### 1.1 Infrastructure
- [x] Project scaffold (manage.py, config/, requirements/, Docker)
- [x] PostgreSQL + PostGIS docker service
- [x] Settings: base / development / production
- [x] Nginx + Gunicorn config

### 1.2 Data Models
- [x] accounts — Custom User, roles (PUBLIC/SELLER/OFFICER/ADMIN)
- [x] groups — NWFPGroup, GroupMember, GroupStatusHistory, Dzongkhag
- [x] products — Product, ProductCategory, ProductImage
- [x] inventory — InventoryBatch, HarvestBatch
- [x] marketplace — Cart, Order, OrderItem, Shipment
- [x] documents — Document, Certificate
- [x] spatial — ResourceSite (PostGIS), SpatialLayer
- [x] approvals — ApprovalRequest, AuditLog, Notification

### 1.3 Views & Workflows
- [x] Marketplace: home, product detail, search, cart, checkout
- [ ] Seller: dashboard, add/edit product, order management
- [x] Officer: group registry, document upload, data imports
- [x] Admin: approval queue, group status, audit log
- [x] Auth: login, register, profile

### 1.4 Data Import
- [x] scripts/import_shapefiles.py — Shapefile → PostGIS ResourceSite
- [x] scripts/import_csv.py — CSV → HarvestBatch (with validation)
- [x] scripts/import_pdfs.py — PDF → Document + metadata
- [x] scripts/import_gpkg.py — GeoPackage → ResourceSite bulk load

### 1.5 Templates & Frontend
- [x] base.html (Tailwind + HTMX + Alpine.js)
- [x] marketplace/home.html — product grid, search, filters
- [x] marketplace/product_detail.html — origin, map, buy
- [x] seller/dashboard.html — mobile-first actions
- [x] management/dashboard.html — approval queue
- [x] partials/ — product_card, cart_items

### 1.6 PWA
- [x] manifest.webmanifest
- [x] service worker (cache recent pages)
- [x] Install prompt

### 1.7 Verification
- [x] Python source compiles with `python -m compileall nwfp_platform`
- [x] JavaScript syntax checks pass for prototype and Django static JS
- [x] Install lightweight local preview Python dependencies
- [x] Run `python manage.py check --settings=config.settings.local_lite`
- [x] Generate migrations and migrate local SQLite database
- [ ] Seed initial groups/products/categories from source data
- [x] Seed minimal local preview product/group/admin data

## Phase 2 — Inventory & Maps
- Inventory batch tracking
- Customer accounts + order tracking
- Leaflet map with group boundaries
- Basic reports (CSV export)
- PWA offline caching

## Phase 3 — Payments & Traceability
- Payment gateway (verify locally first)
- Batch → product traceability
- Reviews
- Push notifications
- Advanced dashboards

## Phase 4 — Analytics
- Overharvest alerts
- Full GIS analytics
- External API integrations

## Tech Stack
| Layer | Tech |
|-------|------|
| Backend | Django 5.x |
| API | Django REST Framework |
| Frontend | Django Templates + HTMX + Alpine.js |
| Styling | Tailwind CSS v3 (CDN for dev, PostCSS for prod) |
| Maps | Leaflet.js |
| Database | PostgreSQL 16 + PostGIS 3 |
| GIS Python | GDAL, Fiona, GeoPandas, django.contrib.gis |
| Auth | django.contrib.auth (custom User) |
| Files | Django FileField + local media (S3-ready) |
| Background | Celery + Redis (Phase 2) |
| Deploy | Docker + Nginx + Gunicorn |

## Data Assets to Import
| File | Target | Script |
|------|--------|--------|
| NWFP_groups_merged.gpkg | ResourceSite + NWFPGroup | import_gpkg.py |
| NWFP Groups Shp Files/ | ResourceSite geometries | import_shapefiles.py |
| management_plans_nwfp/*.pdf | Document model | import_pdfs.py |
| data_csv/*.csv | HarvestBatch | import_csv.py |

## Key Decisions
- AUTH_USER_MODEL = 'accounts.User' (email login, no username)
- Soft delete on Group and Product (never lose data)
- UUIDs as primary keys on core models
- TIME_ZONE = 'Asia/Thimphu'
- Development: SQLite + SpatiaLite fallback; Production: PostGIS
- API versioning: /api/v1/

## Risk Tracking
| Risk | Mitigation |
|------|-----------|
| Payment gateway | Map & display only in Phase 1; confirm gateway before Phase 3 |
| CSV data quality | Strict schema validation + error report on upload |
| GIS accuracy | Import from verified shapefiles only; flag manual entries |
| User adoption | Keep seller dashboard to max 5 actions on home screen |
