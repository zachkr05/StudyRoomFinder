from django.db import models

class ClassInfo(models.Model):
    start_date = models.CharField(max_length=100)
    end_date = models.CharField(max_length=100)
    description = models.TextField()

class MeetingDetail(models.Model):
    class_info = models.ForeignKey(ClassInfo, related_name='meetings', on_delete=models.CASCADE)
    days = models.CharField(max_length=50)
    start_time = models.CharField(max_length=50)
    end_time = models.CharField(max_length=50)
    building_code = models.CharField(max_length=50)
    room = models.CharField(max_length=50)
    facility_description = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255)
