location-recommendation-ai-prototype/
│
├── llm_modules/
│   ├── __init__.py
│   ├── keyword_extraction.py       # Extract keywords from user input via LLM
│   ├── recommendation_engine.py    # Final ranking/recommendation using LLM
│   └── ranking_prompt.py           # Contains prompt templates for ranking
│
├── vector_search/
│   ├── __init__.py
│   ├── qdrant_client.py            # Qdrant connection and search operations
│   └── faiss_module.py             # Optional: FAISS-based vector search functions
│
├── user_analysis/
│   ├── __init__.py
│   ├── user_metadata.py            # Fetches and processes user metadata from Azure
│   └── hidden_insights.py          # Derives hidden user insights or preferences
│
├── place_insights/
│   ├── __init__.py
│   ├── realtime_data.py            # Fetches/synthesizes real-time data (weather, time, etc.) from Azure
│   ├── social_scraping.py          # Fetches/synthesizes social media insights
│   └── distance_metrics.py         # Computes distance between user and places
│
├── aggregation/
│   ├── __init__.py
│   └── aggregate.py                # Aggregates keywords, place, and user data into one prompt
│
├── api/
│   ├── __init__.py
│   └── app.py                      # API entry point (e.g., FastAPI/Flask) for the prototype
│
├── utils/
│   ├── __init__.py
│   ├── azure_client.py             # Handles all Azure cloud operations (SQL/Cosmos/Blob)
│   ├── prompts.py                  # Contains all LLM prompt templates
│   └── helpers.py                  # Helper functions (JSON I/O, config, etc.)
│
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py            # Unit tests for the entire pipeline
│
├── .gitignore                      # Ignore patterns for local artifacts (e.g., .env, __pycache__)
├── README.md                       # Project overview, setup instructions, and team guidelines
└── requirements.txt                # Python dependencies (LangChain, Qdrant, etc.)
