from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Tuple, Union, List


class DistanceCalculator:
    def __init__(self):
        self.EARTH_RADIUS_KM = 6371.0  # Earth's radius in kilometers

    def calculate_haversine_distance(self,
                                     lat1: float,
                                     lon1: float,
                                     lat2: float,
                                     lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in kilometers
        """
        # Convert latitude and longitude to radians
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = self.EARTH_RADIUS_KM * c

        return round(distance, 2)

    def calculate_distances_batch(self,
                                  user_location: Dict[str, float],
                                  places: List[Dict[str, Union[str, float]]]) -> List[Dict[str, Union[str, float]]]:
        """Calculate distances between user location and multiple places.

        Args:
            user_location: Dictionary containing user's latitude and longitude
            places: List of place dictionaries containing coordinates

        Returns:
            List of dictionaries with place IDs and their distances
        """
        results = []
        user_lat = user_location['lat']
        user_lon = user_location['lon']

        for place in places:
            distance = self.calculate_haversine_distance(
                user_lat,
                user_lon,
                place['lat'],
                place['lon']
            )

            results.append({
                'place_id': place.get('id'),
                'distance_km': distance,
                'name': place.get('name')
            })

        return results

    def get_nearby_places(self,
                          user_location: Dict[str, float],
                          places: List[Dict[str, Union[str, float]]],
                          radius_km: float) -> List[Dict[str, Union[str, float]]]:
        """Filter places within a specific radius from user location.

        Args:
            user_location: Dictionary containing user's latitude and longitude
            places: List of place dictionaries containing coordinates
            radius_km: Maximum distance in kilometers

        Returns:
            List of places within the specified radius
        """
        distances = self.calculate_distances_batch(user_location, places)
        return [place for place in distances if place['distance_km'] <= radius_km]

    def calculate_distance_score(self, distance_km: float, max_distance: float = 10.0) -> float:
        """Calculate a normalized score based on distance.

        Args:
            distance_km: Distance in kilometers
            max_distance: Maximum distance to consider (default 10km)

        Returns:
            Score between 0 and 1, where 1 is closest
        """
        if distance_km >= max_distance:
            return 0.0
        return 1.0 - (distance_km / max_distance)
