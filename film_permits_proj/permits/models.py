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

# V2 model: street blocks extracted from Permit.parking_held
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
