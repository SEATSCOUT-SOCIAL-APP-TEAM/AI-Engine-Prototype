from typing import Dict, List, Any
import random
from datetime import datetime, timedelta


class SocialSentimentSimulator:
    def __init__(self):
        self.sentiment_levels = ['positive', 'neutral', 'negative']
        self.sentiment_weights = {'positive': 0.6, 'neutral': 0.3, 'negative': 0.1}

        self.sample_comments = {
            'positive': [
                'Great atmosphere and service!',
                'Absolutely loved this place!',
                'Highly recommended!',
                'Amazing experience, will come back!',
                'Perfect spot for special occasions!'
            ],
            'neutral': [
                'Decent place, nothing special',
                'Average experience',
                'OK for casual visits',
                'Reasonable service and food',
                'Fair prices, standard quality'
            ],
            'negative': [
                'Service could be better',
                'Not worth the price',
                'Expected more from this place',
                'Disappointing experience',
                'Needs improvement'
            ]
        }

    def generate_sentiment_data(self, place_id: str, num_reviews: int = 10) -> Dict[str, Any]:
        """Generate simulated social media sentiment data for a place.

        Args:
            place_id: Identifier for the place
            num_reviews: Number of reviews to generate

        Returns:
            Dictionary containing sentiment analysis and sample reviews
        """
        # Generate weighted random sentiments
        sentiments = random.choices(
            self.sentiment_levels,
            weights=[self.sentiment_weights[s] for s in self.sentiment_levels],
            k=num_reviews
        )

        # Count sentiment frequencies
        sentiment_counts = {
            level: sentiments.count(level) for level in self.sentiment_levels
        }

        # Calculate overall sentiment score (0 to 1)
        total_score = sum(
            sentiment_counts[level] * (idx + 1)
            for idx, level in enumerate(reversed(self.sentiment_levels))
        )
        normalized_score = total_score / (num_reviews * len(self.sentiment_levels))

        # Generate sample reviews
        reviews = []
        for sentiment in sentiments:
            review = {
                'text': random.choice(self.sample_comments[sentiment]),
                'sentiment': sentiment,
                'timestamp': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            reviews.append(review)

        return {
            'place_id': place_id,
            'overall_sentiment': max(sentiment_counts.items(), key=lambda x: x[1])[0],
            'sentiment_score': round(normalized_score, 2),
            'sentiment_distribution': sentiment_counts,
            'recent_reviews': reviews,
            'total_reviews': num_reviews,
            'last_updated': datetime.now().isoformat()
        }

    def get_sentiment_score(self, sentiment_data: Dict[str, Any]) -> float:
        """Extract normalized sentiment score from sentiment data.

        Args:
            sentiment_data: Dictionary containing sentiment analysis

        Returns:
            Normalized sentiment score between 0 and 1
        """
        return sentiment_data.get('sentiment_score', 0.5)

    def batch_generate_sentiments(self, place_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate sentiment data for multiple places.

        Args:
            place_ids: List of place identifiers

        Returns:
            List of sentiment data dictionaries
        """
        return [self.generate_sentiment_data(place_id) for place_id in place_ids]
