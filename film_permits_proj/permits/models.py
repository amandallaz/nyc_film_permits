from django.db import models

class Permit(models.Model):
   event_id = models.CharField(max_length=20, unique=True)
   event_type = models.CharField(max_length=100)
   start_datetime = models.DateTimeField()
   end_datetime = models.DateTimeField()
   parking_held = models.TextField(blank=True)
   borough = models.CharField(max_length=50)
   community_boards = models.CharField(max_length=100, blank=True)
   category = models.CharField(max_length=100)
   subcategory = models.CharField(max_length=100)
   zip_codes = models.CharField(max_length=100)
   # calculated fields
   lat = models.FloatField(null=True, blank=True)
   lon = models.FloatField(null=True, blank=True)

   def __str__(self):
       return f"{self.event_id} - {self.event_type}"