# Mapping NYC Film Permits  

Built an end-to-end data product that transforms raw NYC film permit records into an interactive, street-level map of production activity.

New York City publishes film permit records through the Mayor’s Office of Media and Entertainment via the NYC Open Data portal. While the dataset includes information about productions, dates, and neighborhoods, permit locations are stored as free-text descriptions of street blocks rather than geographic coordinates.

This project builds a data pipeline that transforms those textual records into structured geospatial data, enabling street-level visualization and analysis of filming activity across NYC.

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
- Maps permit activity onto NYC’s street network  
- Enables street-level visualization of filming activity  
- Identifies high-density filming corridors  
- Adds neighborhood-level context for recurring production hotspots  
- Supports interactive filtering and exploration in the map interface  

---

## Tech stack

- Django  
- Python  
- GeoPandas  
- Leaflet (interactive mapping)  
- NYC Open Data API  
- NYC Geoclient API  
- NYC LION street network  
- DigitalOcean (Gunicorn + Nginx)  

---

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
- Time-based filtering via interactive UI  
- Identification of high-density filming corridors  
- Exploration of production patterns across NYC  

---

## Notes

- Designed with a local-first processing model due to the size of geospatial data  
- Production server is optimized for serving precomputed results, not running heavy geospatial processing  
- Demonstrates transforming messy real-world data into structured, analysis-ready features  

---

## Product Direction

This dataset can support:

- Real-time or recent filming activity tracking  
- Analysis of filming density by neighborhood  
- Identification of frequently used production corridors  
