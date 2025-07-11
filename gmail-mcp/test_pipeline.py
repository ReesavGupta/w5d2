import os
import json
from rag_engine import retrieve_relevant_policies, generate_response_with_template

def test_semantic_search():
    print("Testing semantic search...")
    results = retrieve_relevant_policies("refund", top_k=2)
    assert isinstance(results, list) and len(results) > 0, "Semantic search should return results."
    print("Semantic search passed.")

def test_template_response():
    print("Testing template-based response generation...")
    # Use a query that should match a template
    results = retrieve_relevant_policies("refund", top_k=3)
    variables = {"customer_name": "Test User"}
    response = generate_response_with_template("I want a refund", results, variables)
    assert "refund policy" in response.lower() or "eligible for a full refund" in response.lower(), "Template response should mention refund policy."
    print("Template response generation passed.")

def test_llm_fallback():
    print("Testing LLM fallback response generation...")
    # Use a query unlikely to match a template
    results = retrieve_relevant_policies("unrelated query", top_k=3)
    response = generate_response_with_template("This is an unrelated query.", results, {})
    assert isinstance(response, str) and len(response) > 0, "LLM fallback should return a response."
    print("LLM fallback passed.")

def main():
    test_semantic_search()
    test_template_response()
    test_llm_fallback()
    print("\nAll basic pipeline tests passed.")

if __name__ == "__main__":
    main() 