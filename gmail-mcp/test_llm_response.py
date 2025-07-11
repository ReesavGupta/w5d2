from rag_engine import retrieve_relevant_policies, generate_draft_response

def main():
    print("LLM Draft Response Test")
    email = input("Enter a customer email/query: ")
    relevant = retrieve_relevant_policies(email, top_k=3)
    print("\nTop relevant policies/templates:")
    for i, res in enumerate(relevant, 1):
        print(f"\nResult {i}:")
        print(res)
    print("\nGenerating draft response using LLM...")
    response = generate_draft_response(email, relevant)
    print("\nDraft Response:\n")
    print(response)

if __name__ == "__main__":
    main() 