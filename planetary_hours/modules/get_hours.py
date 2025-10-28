from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
from .utils import get_time


PLANETS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

DAY_PLANET = {
    5: "Saturn",    # saturday
    6: "Sun",
    0: "Moon",
    1: "Mars",
    2: "Mercury",
    3: "Jupiter",
    4: "Venus",     # Friday
}

def get_planet_hours(latitude: float, longitude: float, city_name: str, date: str = None):

    location = LocationInfo(
        name=city_name,
        region='Custom',
        timezone="Asia/Tehran",
        latitude=latitude,
        longitude=longitude
    )

    today = datetime.today().date() if not date else get_time(date).date()

    sun_times = sun(
        observer=location.observer,
        date=today,
        tzinfo=location.timezone
    )
    sunrise, sunset = sun_times["sunrise"], sun_times["sunset"]

    tomorrow = today + timedelta(days=1)
    sun_times_tommorow = sun(
        observer=location.observer,
        date=tomorrow,
        tzinfo=location.timezone
    )
    next_sunrise = sun_times_tommorow["sunrise"]

    day_length = (sunset - sunrise) / 12
    night_length = (next_sunrise - sunset) / 12

    weekday = today.weekday()
    first_planet = DAY_PLANET[weekday]
    start_index = PLANETS.index(first_planet)

    hours = []
    current_time = sunrise

    for i in range(12):
        planet = PLANETS[(start_index + i) % 7]
        end_time = current_time + day_length
        hours.append({
            "hour": i + 1, 
            "planet": planet.lower(),
            "start_time": current_time,
            "end_time": end_time
        })
        current_time = end_time

    for i in range(12):
        planet = PLANETS[(start_index + 12 + i) % 7]
        end_time = current_time + night_length
        hours.append({
            "hour": i + 13, 
            "planet": planet.lower(),
            "start_time": current_time,
            "end_time": end_time
        })
        current_time = end_time

    
    return hours

