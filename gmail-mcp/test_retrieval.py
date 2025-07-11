from rag_engine import retrieve_relevant_policies

def main():
    print("Semantic Search Test for Policies/Templates")
    query = input("Enter your query: ")
    results = retrieve_relevant_policies(query, top_k=3)
    print("\nTop relevant policies/templates:")
    for i, res in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(res)

if __name__ == "__main__":
    main() 