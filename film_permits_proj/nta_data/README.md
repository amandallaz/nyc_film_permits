# NYC 2020 Neighborhood Tabulation Areas (NTA)

Used by `assign_segment_nta` to label each `StreetSegment` with a census-style neighborhood.

## Download

1. Open **[NYC Planning — NYNTA2020](https://www.nyc.gov/site/planning/data-maps/open-data/dwn-nynta.page)** or search NYC Open Data for **“2020 Neighborhood Tabulation Areas”**.
2. Download **GeoJSON** (or Shapefile; the command accepts GeoJSON).
3. Save the file here as:

   `nynta2020.geojson`

## Run

From the directory that contains `manage.py`:

```bash
python manage.py assign_segment_nta
```

Custom path:

```bash
python manage.py assign_segment_nta --nta-path /path/to/nta.geojson
```

## Method

- Segment **centroid** must fall **inside** an NTA polygon (WGS84 / EPSG:4326).
- Segments that do not fall in any polygon keep empty `nta_code` / `nta_name` and `nta_match_status=no_match`. **No rows are deleted.**

## Dependencies

`geopandas` and `shapely` (see repo `requirements.txt`).
