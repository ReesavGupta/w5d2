import os
import logging
import json
from datetime import datetime
from main import fetch_unread_emails, mark_email_processed  # FastMCP Gmail tools
from rag_engine import retrieve_relevant_policies, generate_response_with_template

# Configurable batch size
BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", 5))

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/email_responder.log"),
        logging.StreamHandler()
    ]
)
COMPLIANCE_LOG = "logs/email_responder.jsonl"

def log_compliance_entry(entry):
    with open(COMPLIANCE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main():
    logging.info(f"Fetching up to {BATCH_SIZE} unread emails...")
    emails = fetch_unread_emails(max_results=BATCH_SIZE)
    if not emails:
        logging.info("No unread emails found.")
        return
    processed_count = 0
    error_count = 0
    for idx, email in enumerate(emails, 1):
        compliance_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "email_id": email.get('id'),
            "from": email.get('from'),
            "subject": email.get('subject'),
            "snippet": email.get('snippet'),
        }
        try:
            logging.info(f"Processing Email {idx}: From: {email['from']} | Subject: {email['subject']}")
            # Retrieve relevant policies/templates
            relevant = retrieve_relevant_policies(email['snippet'], top_k=3)
            compliance_entry["matched_policies"] = relevant
            # Prompt for variables if a template is found
            variables = {}
            if relevant and all(isinstance(item, dict) for item in relevant):
                for item in relevant:
                    if item.get('type') == 'template' and item.get('page_content'):
                        import re
                        var_names = set(re.findall(r'\{(\w+)\}', item['page_content']))
                        for var in var_names:
                            # For batch, use placeholder or email info (customize as needed)
                            variables[var] = email.get(var, f"<{var}>")
                        break
            # Generate response
            response = generate_response_with_template(email['snippet'], relevant, variables)
            compliance_entry["response"] = response
            compliance_entry["status"] = "processed"
            logging.info(f"Generated Response for Email {idx}:\n{response}")
            # Mark email as processed
            mark_email_processed(email['id'])
            logging.info(f"Email {idx} marked as processed.")
            processed_count += 1
        except Exception as e:
            logging.error(f"Error processing Email {idx}: {e}")
            compliance_entry["status"] = "error"
            compliance_entry["error"] = str(e)
            error_count += 1
        log_compliance_entry(compliance_entry)
    logging.info(f"Batch complete. Processed: {processed_count}, Errors: {error_count}")

if __name__ == "__main__":
    main() 