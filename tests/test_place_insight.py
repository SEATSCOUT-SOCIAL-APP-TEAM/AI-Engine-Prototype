# Import the modules
from place_insights.context_simulator import ContextSimulator
from place_insights.distance_metrics import DistanceCalculator
from place_insights.social_scraping import SocialSentimentSimulator
from qdrant_db.vector_search import VectorSearch
from user_analysis.user_metadata import UserProfileProcessor

# Initialize the components
vector_search = VectorSearch()
user_processor = UserProfileProcessor()
context_sim = ContextSimulator()
distance_calc = DistanceCalculator()
sentiment_analyzer = SocialSentimentSimulator()

# Example user input
user_data = {
    "id": "user_001",
    "preferences": ["lunch", "pet friendly", "air-conditioned", "dessert"],
    "intent": "romantic dinner",
    "personality": "extrovert",
    "mobility": "bike",
    "location": {
        "lat": 10.780282,
        "lon": 106.685861
    },
    "query": "romantic dinner in District 1, Ho Chi Minh City"
}

# Process the search
# # 1. Get semantic search results
search_results = vector_search.semantic_search(user_data["query"], limit=3)

for res in search_results:
    print(res)
#
# for res in search_results:
#     print(res)
#     print("\n==============\n")

# 2. Process user preferences
# user_profile = user_processor.parse_user_data(user_data)
# print(user_profile)

# # 3. Get current context
# context = context_sim.get_current_time_context()
# print(context)

#
# # 4. Calculate rankings for each place

ranked_places = []
for place in search_results:
    # Calculate distance
    distance = distance_calc.calculate_haversine_distance(
        *user_data["location"],
        float(place["payload"]["lat"]), float(place["payload"]["lon"])
    )

    print(distance)

    # Get sentiment
    # sentiment = sentiment_analyzer.get_sentiment(place["id"])
    #
    # # Calculate final score
    # score = calculate_final_score(
    #     semantic_score=place["score"],
    #     distance=distance,
    #     sentiment=sentiment,
    #     context=context,
    #     user_profile=user_profile
    # )

    # ranked_places.append({
    #     "place": place,
    #     "score": score,
    #     "distance": distance,
    #     "sentiment": sentiment
    # })
