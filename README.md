# Mapping NYC Film Permits  

New York City publishes film permit records through the Mayor’s Office of
Media and Entertainment via the NYC Open Data portal. The dataset includes
information about productions, dates, and neighborhoods, but permit locations
are stored as text descriptions of street blocks rather than geographic
coordinates. Additional processing is required before the data
can be mapped or analyzed spatially.


## Overview

    NYC Open Data API
            │
            ▼
          Permit
            │
            ▼
       PermitBlock
            │
            ▼
     block-level coordinates

Permit records are ingested from NYC Open Data, normalized into street
blocks, and geocoded using the NYC Geoclient API.

------------------------------------------------------------------------

## Data Model

### Permit

-   event_id
-   event_type
-   start_datetime
-   end_datetime
-   parking_held
-   borough

### PermitBlock

-   permit (FK)
-   block_order
-   raw_location
-   on_street
-   cross_street_one
-   cross_street_two
-   borough
-   lat
-   lon
-   geocode_status

A single permit may reference many street blocks.

The `PermitBlock` model stores each block separately, enabling more
accurate spatial mapping.

Dataset coverage:          Jan 2023 – Dec 2025  
Dataset last updated:      March 5, 2026  
Permits loaded:            16,024  
PermitBlock rows created:  54,145  
Unique street blocks:      17,344  
Average blocks per permit: 3.38  
Geocoded blocks:           42,218 (~78%)  

------------------------------------------------------------------------

## Data Processing

The system is implemented with Django management commands.

**load_permits**
Fetch permit records from NYC Open Data and store them in the `Permit`
table.

**build_permit_blocks**
Split the `parking_held` field into street blocks.

Example:

    "BROADWAY between WARREN ST and MURRAY ST,
     BROADWAY between CHAMBERS ST and READE ST"

becomes

    PermitBlock
    1 | BROADWAY between WARREN ST and MURRAY ST
    2 | BROADWAY between CHAMBERS ST and READE ST

**geocode_permit_blocks**
Geocode each street block using the NYC Geoclient blockface endpoint.

To reduce API usage, the system geocodes **unique street block + borough
combinations** and applies results to all matching rows.

------------------------------------------------------------------------

## Product Direction

Once locations are structured and geocoded, the dataset can support
applications such as:

-   mapping current filming activity across NYC
-   analyzing filming density by neighborhood
-   identifying streets frequently used for production
