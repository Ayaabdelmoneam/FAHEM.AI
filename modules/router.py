import logging
from typing import Optional

# Optional: if you’re using Tavily or Bing API
from langchain_community.tools.tavily_search.tool import TavilySearchResults


logger = logging.getLogger(__name__)

# ==============================
# 🧠 Intent Classifier
# ==============================
def classify_intent(llm, query: str) -> str:
    """
    Use LLM to classify the user intent into a category.
    """
    system_prompt = """
    Classify the following user query intent into one of:
    [document_query, fact_lookup, chitchat, howto, code]
    Return ONLY the label, no explanation.
    """
    try:
        response = llm.generate_content(f"{system_prompt}\n\nQuery: {query}")
        label = response.text.strip().lower()
        logger.info(f"Intent classified: {label}")
        return label
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return "document_query"  # default fallback


# ==============================
# 📊 Relevance Judge
# ==============================
def judge_answer_relevance(llm, query: str, answer: str) -> bool:
    """
    Uses the LLM to evaluate whether the generated answer actually
    addresses the user's query in a meaningful way.
    Returns True if it does, False otherwise.
    """
    prompt = f"""
        You are a critical evaluator. Your task is to judge whether the following answer
        actually provides information that addresses the user query.

        Query:
        {query}

        Answer:
        {answer}

        Answer only with "YES" if the answer addresses the question meaningfully,
        or "NO" if the answer is irrelevant, vague, or fails to provide the requested information.
            """

    response = llm.generate_content(prompt)  # adjust this line to your LLM call signature

    # decision = response.strip().upper()
    return response.text.strip().lower().startswith("y") # YES → relevant

def judge_relevance(llm, query: str, context: str) -> bool:
    """
    Ask LLM whether the retrieved context is relevant to the query.
    """
    prompt = f"""
    Determine if the following context is RELEVANT and CONTAINS
    information that can answer the user query.

    Query: {query}

    Context:
    {context}
    Answer only with YES or NO.
    """
    try:
        response = llm.generate_content(prompt)
        print(f"Relevance judge response: {response.text}")
        return response.text.strip().lower().startswith("y")
    except Exception as e:
        logger.error(f"Relevance judging failed: {e}")
        return False


# ==============================
# 🌐 Web Search Agent
# ==============================
# config.py
TAVILY_API_KEY = ""

def web_search_agent(query: str) -> str:
    """
    Retrieve relevant information from the web using Tavily or any search API.
    Returns aggregated search results as text context.
    """
    try:
        search = TavilySearchResults(tavily_api_key=TAVILY_API_KEY,max_results=3)
        results = search.run(query)
        if isinstance(results, list):
            # Tavily returns list of dicts
            context = "\n\n".join([r.get("content", "") for r in results])
        else:
            context = str(results)
        return context
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return ""


# ==============================
# 🚦 Router
# ==============================
def router(llm, retrieved ,internal_answer, query: str, min_score_threshold: float = 0.4) -> dict:
    """
    Decides whether to use internal RAG or web search.
    Returns dict with:
    {
        "mode": "internal" | "web",
        "context": str
    }
    """
    # 1. Classify intent
    # intent = classify_intent(llm, query)

    # 2. Retrieve internal knowledge
    # retrieval = rag.retrieve(query, top_k=3)
    # retrieved_docs = retrieved

    # 3. Default: use internal RAG
    # route_to_web = False
    # context = ""

    # 4. Routing rules
    # top_score, context = retrieved["score"], retrieved["context"]


    top_score = retrieved[0].get("score", 0)
    print(f"Top retrieval score: {top_score}")
    context = "\n\n".join([d.get("content", "") for d in retrieved])

    route = {"mode": "internal", "context": context, "answer": None}

    # 3️⃣ If retrieval score is too low, skip internal completely
    if top_score < min_score_threshold:
        logger.info(f"Low similarity ({top_score:.2f}) → route to web.")
        route["mode"] = "web"
        return route

    # 4️⃣ Generate internal answer using your Colab RAG model
    route["answer"] = internal_answer

    # 5️⃣ Use LLM to judge whether the answer actually addresses the query
    is_relevant = judge_answer_relevance(llm, query, internal_answer)
    print(f"LLM judge relevance: {is_relevant}")

    if not is_relevant:
        logger.info("LLM judge determined the internal answer does NOT address the query → routing to web.")
        route["mode"] = "web"
        route["context"] = web_search_agent(query) # clear context if switching to web
    return route
