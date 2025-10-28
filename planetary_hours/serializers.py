from rest_framework import serializers


class PlanetRequestQuerySerizlier(serializers.Serializer):
    lat = serializers.FloatField(required=True)
    lon = serializers.FloatField(required=True)
    city = serializers.CharField(required=True)
    date = serializers.CharField(required=False)


class PlanetHoursSerizlier(serializers.Serializer):
    hour = serializers.IntegerField()
    planet = serializers.CharField(max_length=50)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()