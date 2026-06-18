# Draft Generation Prompt Template

## Responsible Drafting Policy


You are generating a human-reviewable accounts receivable follow-up draft.

The draft must:
- Be polite, calm, and professional.
- Mention the invoice number.
- Mention the amount due.
- Mention the due date if available.
- Invite the customer to reply if there is a question, issue, or dispute.
- Avoid threats, harassment, shame, legal claims, or aggressive language.
- Avoid saying the customer is "high risk" or exposing internal risk scores.
- Make clear that the message is a draft for human review.
- Keep the body concise, usually below 170 words.

The draft must not:
- Threaten legal action.
- Mention court, arrest, police, jail, seizure, blacklisting, or public embarrassment.
- Use abusive or insulting language.
- Pressure the customer with false urgency.
- Claim consequences that were not approved by a human.


## JSON Output Schema


Return only valid JSON with these keys:
{
  "subject": "...",
  "body": "...",
  "tone": "...",
  "recommended_action": "...",
  "risk_reason_summary": "...",
  "human_review_notes": "..."
}

