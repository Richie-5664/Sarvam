import time
from typing import Any, Dict, Optional
from vpod.client import get_sarvam_client
from vpod.document_parser import DocumentParser
from vpod.audio_transcriber import AudioTranscriber
from vpod.verifier import PODVerifier
from sarvamai import SarvamAI


class VoicePODPipeline:
    """End-to-end Voice Proof-of-Delivery pipeline combining Document AI, STT, and Sarvam-105B."""

    def __init__(self, client: Optional[SarvamAI] = None):
        self.client = client or get_sarvam_client()
        self.doc_parser = DocumentParser(self.client)
        self.audio_transcriber = AudioTranscriber(self.client)
        self.verifier = PODVerifier(self.client)

    def verify(
        self,
        document_path: str,
        audio_path: str,
        order_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the end-to-end Voice Proof-of-Delivery verification.

        Args:
            document_path: Path to photo/scan of paper delivery receipt or challan.
            audio_path: Path to voice recording of delivery confirmation.
            order_metadata: Optional order management system metadata.

        Returns:
            Dict containing the final audit decision, parsed documents, transcripts, and timing.
        """
        start_total = time.time()

        # Step 1: Parse paper POD via Sarvam Vision 1.5
        t0 = time.time()
        doc_result = self.doc_parser.parse_pod_document(document_path)
        doc_duration = time.time() - t0

        # Step 2: Transcribe voice confirmation via Saaras v4 STT
        t1 = time.time()
        audio_result = self.audio_transcriber.transcribe_voice_confirmation(audio_path)
        audio_duration = time.time() - t1

        # Step 3: Reason & Cross-Examine via Sarvam-105B
        t2 = time.time()
        audit_verdict = self.verifier.verify(
            document_data=doc_result.get("fields", {}),
            audio_data=audio_result,
            order_metadata=order_metadata,
        )
        audit_duration = time.time() - t2

        total_duration = time.time() - start_total

        return {
            "verdict": audit_verdict,
            "document_extraction": doc_result,
            "audio_transcription": audio_result,
            "timings": {
                "document_ai_seconds": round(doc_duration, 2),
                "speech_to_text_seconds": round(audio_duration, 2),
                "reasoning_seconds": round(audit_duration, 2),
                "total_seconds": round(total_duration, 2),
            },
        }

    @staticmethod
    def format_report(result: Dict[str, Any]) -> str:
        """Format the pipeline result into an executive logistics audit report."""
        verdict = result.get("verdict", {})
        doc = result.get("document_extraction", {}).get("fields", {})
        audio = result.get("audio_transcription", {})
        timings = result.get("timings", {})

        status = verdict.get("status", "UNKNOWN")
        flags = verdict.get("flags", [])
        status_symbol = "✅" if status == "VERIFIED" else ("⚠️" if status == "FLAGGED_EXCEPTION" else "❌")

        lines = [
            "=" * 60,
            f"  VOICE PROOF-OF-DELIVERY (vPOD) AUDIT REPORT",
            "=" * 60,
            f"Status:       {status_symbol} {status}",
            f"Confidence:   {verdict.get('confidence', 0.0) * 100:.1f}%",
            f"Recipient:    {verdict.get('recipient_classification', 'UNKNOWN')}",
            f"Flags:        {', '.join(flags) if flags else 'None (Clean Delivery)'}",
            "-" * 60,
            "1. PAPER POD (Sarvam Vision 1.5):",
            f"   Consignee Name:     {doc.get('consignee_name', 'N/A')}",
            f"   AWB / Tracking:     {doc.get('awb_number', 'N/A')}",
            f"   Delivery Address:   {doc.get('delivery_address', 'N/A')}",
            f"   Signature Present:  {doc.get('signature_present', False)}",
            "-" * 60,
            "2. VOICE CONFIRMATION (Sarvam Saaras v4):",
            f"   Detected Language:  {audio.get('language_code', 'unknown')}",
            f"   Spoken Transcript:  \"{audio.get('transcript', '')}\"",
            f"   English Translated: \"{audio.get('translated_transcript', '')}\"",
            "-" * 60,
            "3. COMPLIANCE REASONING (Sarvam-105B):",
            f"   Summary:    {verdict.get('summary', '')}",
            f"   Reasoning:  {verdict.get('reasoning', '')}",
            "-" * 60,
            f"Execution Times: Document AI: {timings.get('document_ai_seconds', 0)}s | STT: {timings.get('speech_to_text_seconds', 0)}s | LLM: {timings.get('reasoning_seconds', 0)}s | Total: {timings.get('total_seconds', 0)}s",
            "=" * 60,
        ]
        return "\n".join(lines)
