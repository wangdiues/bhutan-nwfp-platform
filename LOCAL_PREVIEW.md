# Local Django Preview

This preview runs the Django app without Docker/PostGIS by using SQLite and
`config.settings.local_lite`. GIS endpoints are replaced with a placeholder page.

## Install lightweight dependencies

```powershell
cd "E:\Bhutan NWFP Web Marketplace and Management Platform\nwfp_platform"
python -m pip install --user -r requirements\local.txt
```

## Prepare the local database

```powershell
python manage.py migrate --settings=config.settings.local_lite
```

Optional demo admin:

```powershell
python manage.py createsuperuser --settings=config.settings.local_lite
```

Current seeded preview login:

```text
Email: admin@nwfp.local
Password: admin12345
```

## Run

```powershell
python manage.py runserver 127.0.0.1:8005 --settings=config.settings.local_lite
```

Open:

```text
http://127.0.0.1:8005/
http://127.0.0.1:8005/products/
http://127.0.0.1:8005/admin/
```

For full GIS/PostGIS behavior, install Docker and use the normal
`docker-compose.yml` stack instead of local lite mode.
