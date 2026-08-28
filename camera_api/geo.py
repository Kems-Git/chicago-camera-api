import math

EARTH_RADIUS_METERS = 6371000


def flat_earth_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    avg_lat_rad = math.radians((lat1 + lat2) / 2)

    x = math.radians(lon2 - lon1) * math.cos(avg_lat_rad)
    y = math.radians(lat2 - lat1)

    return EARTH_RADIUS_METERS * math.sqrt(x**2 + y**2)


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    avg_lat_rad = math.radians((lat1 + lat2) / 2)

    x = math.radians(lon2 - lon1) * math.cos(avg_lat_rad)
    y = math.radians(lat2 - lat1)

    theta = math.atan2(x, y)

    return (math.degrees(theta) + 360) % 360


def classify_relative_position(bearing: float, heading: float) -> str:
    relative_angle = (bearing - heading) % 360

    if relative_angle <= 45 or relative_angle > 315:
        return "ahead"
    if relative_angle <= 135:
        return "right"
    if relative_angle <= 225:
        return "behind"
    return "left"
