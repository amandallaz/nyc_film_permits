# Mapping NYC Film Permits  
Transform raw NYC film permit records into an interactive, street level map of production activity.

Live: https://amandalaz.com/filming-streets/

![Filming Streets Map](https://github.com/user-attachments/assets/ff65cc9c-5680-495a-b637-f2f611ca1e94)

New York City publishes film permit records through the Mayor’s Office of Media and Entertainment via the NYC Open Data portal. The dataset includes information about productions, dates, and neighborhoods. Permit locations are stored as text descriptions of street blocks rather than geographic coordinates. This project builds a data pipeline that transforms those text records into structured geospatial data, enabling street level visualization and analysis of filming activity across NYC.

---

## Overview

    NYC Open Data API
        ↓
    Raw permit records
        ↓
    Parsed street blocks
        ↓
    Geocoded block locations
        ↓
    Matched street segments (LION)
        ↓
    Segment-level filming activity
        ↓
    Interactive map

---

## What this project does

- Transforms unstructured permit location text into structured geospatial data  
- Maps permit activity onto NYC’s LION street network  
- Enables street-level visualization of filming activity  
    - Identifies high-density filming corridors  
    - Adds neighborhood-level context for recurring production hotspots  
    - Supports interactive filtering and exploration in the map interface  

---

## Tech stack

- Django  
- Python  
- GeoPandas  
- MapLibre + deck.gl 
- NYC Open Data API  
- NYC Geoclient API  
- NYC LION street network  
- DigitalOcean (Gunicorn + Nginx)  

---

## Quickstart

### Setup

```bash
git clone https://github.com/amandallaz/nyc_film_permits.git
cd nyc_film_permits

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Initialize the app

```bash
cd film_permits_proj
python manage.py migrate
```

### Build the dataset (local)

```bash
python manage.py load_permits
python manage.py build_permit_blocks
python manage.py geocode_permit_blocks
python manage.py load_lion_segments
python manage.py match_block_segments
python manage.py assign_segment_nta
```

### Run locally

```bash
python manage.py runserver
```

Open:
- http://127.0.0.1:8000/filming-streets/

---

## Deploy

This project uses a **local-first deployment model**:

- heavy geospatial processing runs locally  
- production serves precomputed results  

This keeps deployment fast and avoids running memory-intensive GeoPandas workflows on a small server.

---

### 1. Rebuild data locally if needed

```bash
python manage.py load_permits
python manage.py build_permit_blocks
python manage.py geocode_permit_blocks
python manage.py load_lion_segments
python manage.py match_block_segments
python manage.py assign_segment_nta
```

---

### 2. Transfer database to server

Run from your local machine:

```bash
scp path/to/db.sqlite3 user@your-server:/path/to/project/
```

---

### 3. Update and restart server

```bash
ssh user@your-server

# set correct permissions
chown user:user /path/to/project/db.sqlite3

# update code
cd /path/to/project
git pull origin master (or main or your deploy branch)

# activate environment
source venv/bin/activate
cd film_permits_proj

# apply migrations
python manage.py migrate

# restart services
python manage.py collectstatic --noinput
sudo systemctl restart app_name
sudo systemctl restart nginx
```

---

### 4. Verify

Open your deployed app:

```text
https://your-domain.com/filming-streets/
```

---

### Notes

- If routes change, update Django `urls.py` and your reverse proxy configuration 

## Data Model

### Permit  
Raw records from NYC Open Data.

- event_id  
- event_type  
- start_datetime  
- end_datetime  
- parking_held  
- borough  

---

### PermitBlock  

- permit (FK)  
- block_order  
- raw_location  
- on_street  
- cross_street_one  
- cross_street_two  
- borough  
- lat  
- lon  
- geocode_status  

A single permit can generate multiple PermitBlock rows.

---

### StreetSegment  

- segment_id  
- geometry (LineString)  
- borough  
- permit_count  
- nta (optional)  

Represents the NYC street network (LION), enriched with aggregated filming activity.

---

## Dataset Snapshot

- Coverage: Jan 2023 – Dec 2025  
- Last updated: March 5, 2026  
- Permits: 16,024  
- PermitBlock rows: 54,145  
- Unique street blocks: 17,344  
- Avg blocks per permit: 3.38  
- Geocoded blocks: 42,218 (~78%)  

---

## Data Pipeline

The pipeline is implemented with Django management commands:

- load_permits  
  Ingest permit records from NYC Open Data  

- build_permit_blocks  
  Parse the parking_held field into structured street blocks  

- geocode_permit_blocks  
  Convert street blocks into coordinates using NYC Geoclient  

- load_lion_segments  
  Load NYC’s official street centerline dataset (LION)  

- match_block_segments  
  Match permit blocks to real street segments  

- assign_segment_nta (optional)  
  Enrich segments with neighborhood context  

To reduce API usage, geocoding is deduplicated across unique street block + borough combinations.

---

## Output

The final dataset supports:

- Street-level visualization of filming activity  
- Filtering via interactive UI  
- Identification of high-density filming corridors  
- Exploration of production patterns across NYC   

---

## Product Direction

This dataset can support:

- Real-time or recent filming activity tracking  
- Analysis of filming density by neighborhood  
- Identification of frequently used production corridors  
