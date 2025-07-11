import json
from rag_engine import retrieve_relevant_policies, generate_response_with_template

def main():
    print("Template-Based Response Generation Test")
    email = input("Enter a customer email/query: ")
    relevant = retrieve_relevant_policies(email, top_k=3)
    print("\nTop relevant policies/templates:")
    for i, res in enumerate(relevant, 1):
        print(f"\nResult {i}:")
        print(res.get('page_content', res))
    # Prompt for variables if a template is found
    variables = {}
    # Only proceed if all items in relevant are dicts
    if relevant and all(isinstance(item, dict) for item in relevant):
        for item in relevant:
            if item.get('type') == 'template' and item.get('page_content'):
                import re
                var_names = set(re.findall(r'\{(\w+)\}', item['page_content']))
                for var in var_names:
                    variables[var] = input(f"Enter value for '{var}': ")
                break
        print("\nGenerating response...")
        response = generate_response_with_template(email, relevant, variables)
    else:
        # Fallback: treat as semantic search only
        print("\n[No template found or semantic search returned only strings.]")
        response = "[No template found. Semantic search results only.]"
    print("\nFinal Response:\n")
    print(response)

if __name__ == "__main__":
    main() 