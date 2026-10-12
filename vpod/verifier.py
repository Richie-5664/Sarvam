import json
import re
from typing import Any, Dict, List, Optional
from sarvamai import SarvamAI


VERIFICATION_SYSTEM_PROMPT = """You are an automated logistics audit and compliance AI specializing in Proof-of-Delivery (POD) verification for Indian logistics networks.

You will be given:
1. Paper POD document fields extracted via Sarvam Vision 1.5 OCR (consignee name, signature presence, AWB).
2. Voice confirmation transcript and translation captured at the doorstep via Sarvam Saaras v4 STT.

Your task is to cross-examine both sources to detect discrepancies, legal compliance, and operational exceptions.

Evaluate the following rules:
- CONSIGNEE IDENTITY: Compare the spoken recipient's identity with the consignee name on the paper document. Distinguish between the named consignee, an authorized proxy (e.g. spouse, neighbor, security guard, housemate), or an unauthorized/conflicting individual.
- SIGNATURE AUDIT: Check if signature_present is true. If false, flag MISSING_SIGNATURE.
- DAMAGE / ANOMALY DETECTION: Listen for spoken mentions of damaged packaging, unsealed boxes, wrong items, missing items, or delivery disputes.
- VERDICT STATUS:
  - "VERIFIED": Named consignee or valid proxy accepted with signature and no package damage.
  - "FLAGGED_EXCEPTION": Proxy delivery without prior authorization, missing signature, package damage mentioned, or partial delivery.
  - "REJECTED": Explicit refusal, completely unrecognized recipient, or dispute over non-delivery.

Always reply in strictly valid JSON format matching this schema:
{
  "status": "VERIFIED" | "FLAGGED_EXCEPTION" | "REJECTED",
  "recipient_classification": "NAMED_CONSIGNEE" | "PROXY_FAMILY" | "PROXY_NEIGHBOR_SECURITY" | "UNKNOWN",
  "flags": ["FLAG_CODE_1", "FLAG_CODE_2"],
  "confidence": 0.95,
  "summary": "Concise summary of findings.",
  "reasoning": "Step-by-step audit rationale.",
  "legal_audit_log": {
    "paper_consignee": "...",
    "spoken_identity": "...",
    "signature_verified": true | false,
    "condition_intact": true | false
  }
}
Do not include any Markdown code blocks or extraneous text outside the JSON object."""


class PODVerifier:
    """Verifies paper document data against voice confirmation using Sarvam-105B."""

    def __init__(self, client: SarvamAI):
        self.client = client

    def verify(
        self,
        document_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        order_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Cross-examine document data and voice confirmation to produce an auditable verdict.

        Args:
            document_data: Extracted fields from DocumentParser (consignee_name, signature_present, etc.).
            audio_data: Transcription details from AudioTranscriber (transcript, translation, language).
            order_metadata: Optional order management metadata (order_id, delivery_partner, etc.).

        Returns:
            Dict containing verification status, exception flags, summary, and audit log.
        """
        payload = {
            "document_extracted_data": document_data,
            "voice_confirmation_data": audio_data,
            "order_metadata": order_metadata or {},
        }

        user_content = (
            "Analyze the following Proof-of-Delivery data and generate the compliance audit:\n"
            f"{json.dumps(payload, indent=2, ensure_ascii=False, default=str)}"
        )

        response = self.client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[
                {"role": "system", "content": VERIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
        )

        raw_reply = response.choices[0].message.content or "{}"

        # Clean JSON markdown fences if present
        clean_json_str = raw_reply.strip()
        if clean_json_str.startswith("```"):
            clean_json_str = re.sub(r"^```(?:json)?\n?", "", clean_json_str)
            clean_json_str = re.sub(r"\n?```$", "", clean_json_str)

        try:
            return json.loads(clean_json_str)
        except json.JSONDecodeError:
            return {
                "status": "FLAGGED_EXCEPTION",
                "recipient_classification": "UNKNOWN",
                "flags": ["PARSE_ERROR"],
                "confidence": 0.5,
                "summary": "LLM response was not valid JSON.",
                "reasoning": raw_reply,
                "legal_audit_log": {},
            }
