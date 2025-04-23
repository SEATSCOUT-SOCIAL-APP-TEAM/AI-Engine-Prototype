from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class UserLocation:
    lat: float
    lon: float


@dataclass
class UserProfile:
    id: str
    preferences: List[str]
    intent: str
    personality: str
    mobility: str
    location: UserLocation
    query: str


class UserProfileProcessor:
    def __init__(self):
        # Mobility distance limits (in kilometers)
        self.mobility_limits = {
            'walk': 2.0,
            'bike': 5.0,
            'car': 20.0,
            'public_transport': 15.0
        }

    def parse_user_data(self, user_data: Dict[str, Any]) -> UserProfile:
        """Parse raw user data into UserProfile object."""
        location = UserLocation(
            lat=user_data['location']['lat'],
            lon=user_data['location']['lon']
        )

        return UserProfile(
            id=user_data['id'],
            preferences=user_data['preferences'],
            intent=user_data['intent'],
            personality=user_data['personality'],
            mobility=user_data['mobility'],
            location=location,
            query=user_data['query']
        )

    def get_mobility_limit(self, user_profile: UserProfile) -> float:
        """Get maximum distance limit based on user's mobility preference."""
        return self.mobility_limits.get(user_profile.mobility.lower(), float('inf'))

    def extract_time_context(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Extract time-related context from user profile."""
        return {
            'time_of_day': user_profile.time_of_day,
            'is_evening': user_profile.time_of_day.lower() == 'evening',
            'is_morning': user_profile.time_of_day.lower() == 'morning',
        }

    def get_preference_weights(self, user_profile: UserProfile) -> Dict[str, float]:
        """Generate weights for different user preferences."""
        weights = {
            'semantic_match': 1.0,
            'distance': 0.8,
            'preference_match': 0.9,
            'intent_match': 1.0,
            'time_context': 0.7,
            'social_sentiment': 0.6
        }

        # Adjust weights based on personality
        if user_profile.personality.lower() == 'extrovert':
            weights['social_sentiment'] = 0.8

        return weights

    def calculate_preference_match_score(self, user_profile: UserProfile, place_tags: List[str]) -> float:
        """Calculate how well a place matches user preferences."""
        if not user_profile.preferences or not place_tags:
            return 0.0

        matching_tags = set(user_profile.preferences) & set(place_tags)
        return len(matching_tags) / len(user_profile.preferences)
