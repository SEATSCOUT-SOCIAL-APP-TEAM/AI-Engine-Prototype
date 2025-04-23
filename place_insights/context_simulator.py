from typing import Dict, Any
from datetime import datetime, time
import random


class ContextSimulator:
    def __init__(self):
        self.weather_conditions = [
            'sunny', 'cloudy', 'rainy', 'windy', 'clear'
        ]

        self.time_periods = {
            'morning': (time(6, 0), time(11, 59)),
            'afternoon': (time(12, 0), time(16, 59)),
            'evening': (time(17, 0), time(21, 59)),
            'night': (time(22, 0), time(5, 59))
        }

    def get_current_weather(self) -> Dict[str, Any]:
        """Simulate current weather conditions.

        Returns:
            Dictionary containing weather information
        """
        condition = random.choice(self.weather_conditions)
        temperature = round(random.uniform(20.0, 35.0), 1)  # Simulated temperature in Celsius

        return {
            'condition': condition,
            'temperature': temperature,
            'is_outdoor_friendly': condition not in ['rainy', 'windy'],
            'timestamp': datetime.now().isoformat()
        }

    def get_current_time_context(self) -> Dict[str, Any]:
        """Get current time period and related context.

        Returns:
            Dictionary containing time-related context
        """
        current_time = datetime.now().time()

        # Determine current time period
        current_period = 'night'  # default
        for period, (start, end) in self.time_periods.items():
            if start <= current_time <= end:
                current_period = period
                break

        return {
            'time_period': current_period,
            'is_business_hours': 8 <= current_time.hour <= 20,
            'timestamp': datetime.now().isoformat(),
            'hour': current_time.hour
        }

    def check_place_availability(self, opening_hours: list, busy_hours: list) -> Dict[str, Any]:
        """Check if a place is currently open and its crowding status.

        Args:
            opening_hours: List containing opening and closing times ['HH:MM', 'HH:MM']
            busy_hours: List of typically busy hours [int]

        Returns:
            Dictionary containing availability information
        """
        current_time = datetime.now().time()
        current_hour = current_time.hour

        # Parse opening hours
        if opening_hours and len(opening_hours) == 2:
            opening_time = datetime.strptime(opening_hours[0], '%H:%M').time()
            closing_time = datetime.strptime(opening_hours[1], '%H:%M').time()
            is_open = opening_time <= current_time <= closing_time
        else:
            is_open = True  # Default to open if no hours provided

        return {
            'is_open': is_open,
            'is_busy_hour': current_hour in busy_hours,
            'crowding_level': 'high' if current_hour in busy_hours else 'low',
            'timestamp': datetime.now().isoformat()
        }

    def get_full_context(self, opening_hours: list = None, busy_hours: list = None) -> Dict[str, Any]:
        """Get complete context including weather and time information.

        Args:
            opening_hours: Optional list of opening hours
            busy_hours: Optional list of busy hours

        Returns:
            Dictionary containing all context information
        """
        context = {
            'weather': self.get_current_weather(),
            'time': self.get_current_time_context()
        }

        if opening_hours is not None and busy_hours is not None:
            context['availability'] = self.check_place_availability(opening_hours, busy_hours)

        return context
