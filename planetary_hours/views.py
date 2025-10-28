from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import PlanetHoursSerizlier, PlanetRequestQuerySerizlier
from .modules.get_hours import get_planet_hours


@api_view(["GET"])
def get_hours(request):
    request_query_serilizer = PlanetRequestQuerySerizlier(data=request.query_params)
    request_query_serilizer.is_valid(raise_exception=True)
    query_data = request_query_serilizer.validated_data

    planet_hours = get_planet_hours(
        latitude=query_data["lat"],
        longitude=query_data["lon"],
        city_name=query_data["city"],
        date=query_data.get("date")
    )

    serializer = PlanetHoursSerizlier(planet_hours, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)