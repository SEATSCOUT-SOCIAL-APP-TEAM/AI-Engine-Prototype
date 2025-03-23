### 1. **User Input Reception**
- **Entry Point:** `api/app.py` (or an optional `main.py` if running as a CLI)
- **What Happens:**
  - The API receives a POST request (or a CLI command) with a JSON payload. For example:
    ```json
    {
      "query": "Find me a cozy coffee shop near me with good ambiance."
    }
    ```
  - This input may include optional metadata (like location coordinates) for distance calculations.
- **Next Step:** The API forwards the input to the **Keyword Extraction** module.

---

### 2. **Keyword Extraction**
- **Module:** `llm_modules/keyword_extraction.py`
- **What Happens:**
  - The module processes the user query using an LLM (via Groq, OpenAI, or Llama) to extract core keywords (e.g., "cozy", "coffee shop", "good ambiance").
  - **Example Outcome:** `["cozy", "coffee shop", "ambiance"]`
- **Next Step:** These keywords are then used as a basis for fetching relevant data.

---

### 3. **Fetching Data from Azure Cloud**
Data is not stored locally; it’s fetched on-demand from your Azure services. This step is split into two parallel pipelines:

#### A. **Place Insights Pipeline**
- **Modules Involved:**
  - `place_insights/realtime_data.py`: Retrieves contextual data like current weather, time of day, etc.
  - `place_insights/social_scraping.py`: Fetches or synthesizes social media sentiment and popularity metrics for places.
  - `place_insights/distance_metrics.py`: Uses the user’s location to calculate distances to nearby places.
- **Azure Integration:**
  - These modules call functions from `utils/azure_client.py` to query Azure databases (like Azure SQL or CosmosDB) for up-to-date place data.
- **Outcome:** A structured JSON containing enriched place data for each candidate location.

#### B. **User Analysis Pipeline**
- **Modules Involved:**
  - `user_analysis/user_metadata.py`: Retrieves the user's profile details from Azure.
  - `user_analysis/hidden_insights.py`: Analyzes or retrieves hidden user insights (e.g., past behavior, preferences).
- **Azure Integration:**
  - Similarly, these modules use the `azure_client.py` to get the relevant user data.
- **Outcome:** A structured JSON with user-specific insights that reflect personality traits and behavior patterns.

---

### 4. **Optional Vector Search**
- **Module:** `vector_search/qdrant_client.py` (or `faiss_module.py` if you choose FAISS)
- **What Happens:**
  - The extracted keywords (or their embeddings) may be used to perform a semantic similarity search against an indexed vector database (if you choose to include this feature).
  - This can narrow down or rank candidate places based on similarity to the query.
- **Outcome:** A refined list of candidate places based on semantic closeness.

---

### 5. **Aggregation of Data**
- **Module:** `aggregation/aggregate.py`
- **What Happens:**
  - The outputs from the **Keyword Extraction**, **Place Insights**, and **User Analysis** pipelines are collected.
  - This module combines all pieces into a single JSON object that contains:
    - Extracted keywords
    - User metadata and insights
    - Place contextual data (including real-time and social media insights)
  - **Example Aggregated Data Structure:**
    ```json
    {
      "keywords": ["cozy", "coffee shop", "ambiance"],
      "user": { ... },
      "places": [
         { "id": "place1", "distance": "0.5 km", "weather": "clear", "social_score": 8, ... },
         { "id": "place2", ... }
      ]
    }
    ```

---

### 6. **LLM-Based Ranking & Recommendation**
- **Module:** `llm_modules/recommendation_engine.py`
- **What Happens:**
  - This module uses the aggregated data along with prompt templates (from `llm_modules/ranking_prompt.py` and/or `utils/prompts.py`) to construct a detailed prompt for the LLM.
  - The LLM is then called to rank or recommend the top locations based on:
    - Relevance of keywords to place attributes
    - User profile and hidden insights (for personalization)
    - Contextual factors like distance and real-time conditions
  - **Example LLM Prompt Snippet:**
    ```
    Given the user's preferences and the following details about each location:
    [List of places with attributes],
    Please rank and recommend the best places that match the user’s query.
    ```
  - **Outcome:** A ranked list (e.g., top 2-3 recommendations) with detailed reasoning if needed.

---

### 7. **Returning the Result**
- **Back to:** `api/app.py`
- **What Happens:**
  - The final recommendation from the LLM is sent back as a JSON response to the API caller.
  - **Example JSON Response:**
    ```json
    {
      "recommendations": [
        {"place_id": "place1", "name": "Cozy Cafe", "score": 9.2},
        {"place_id": "place2", "name": "Sunny Coffee", "score": 8.7}
      ]
    }
    ```

---

### 8. **Testing the Pipeline**
- **Module:** `tests/test_pipeline.py`
- **What Happens:**
  - Unit tests are run to simulate the complete workflow.
  - Tests validate:
    - The correct extraction of keywords.
    - Successful data retrieval from Azure.
    - Proper aggregation of data.
    - Valid response from the recommendation engine.
- **Purpose:** Ensure that each module works correctly both individually and as part of the overall pipeline.

---

### **Cloud Integration Summary**
- **Azure Client:**  
  All Azure interactions are centralized in `utils/azure_client.py`, ensuring that every data fetch (user, place, real-time) uses a consistent connection method. This module abstracts away connection details and makes it easy to swap or update Azure service configurations.

- **Modularity:**  
  Each pipeline component (keyword extraction, user analysis, place insights) works independently, so you can update or scale them without affecting the others.

- **Extensibility:**  
  Adding vector search or additional data sources in the future will be straightforward, thanks to the clear separation of concerns.
