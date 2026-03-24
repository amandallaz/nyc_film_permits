from django.db import models
   
class Permit(models.Model):
    event_id = models.CharField(max_length=20, unique=True)
    event_type = models.CharField(max_length=100)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    parking_held = models.TextField(blank=True)
    borough = models.CharField(max_length=50, blank=True)
    community_boards = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    subcategory = models.CharField(max_length=100, blank=True)
    zip_codes = models.TextField(blank=True)
    # V1 approximate permit midpoint
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.event_id} - {self.event_type}"

# V2 model: street blocks extracted from Permit.parking_held, (event table)
class PermitBlock(models.Model):
    permit = models.ForeignKey(
        Permit,
        on_delete=models.CASCADE,
        related_name="blocks"
    )
    block_order = models.IntegerField()
    raw_location = models.TextField()
    borough = models.CharField(max_length=50, blank=True)
    on_street = models.CharField(max_length=255, blank=True)
    cross_street_one = models.CharField(max_length=255, blank=True)
    cross_street_two = models.CharField(max_length=255, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    geocode_status = models.CharField(max_length=50, blank=True)
    segment_id = models.CharField(max_length=50, blank=True)
    segment_match_status = models.CharField(max_length=50, blank=True)

# geo table of street segments
# https://www.nyc.gov/content/planning/pages/resources/datasets/lion
class StreetSegment(models.Model):
    segment_id = models.CharField(max_length=50, unique=True)
    street = models.CharField(max_length=255, blank=True)
    borough = models.CharField(max_length=50, blank=True)
    geometry_geojson = models.JSONField()
    permit_count = models.IntegerField(default=0)
    # NYC Planning 2020 Neighborhood Tabulation Areas (NTA), via centroid-in-polygon join
    nta_code = models.CharField(max_length=20, blank=True)
    nta_name = models.CharField(max_length=255, blank=True)
    nta_match_status = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.street} ({self.segment_id})"