import json
import mimetypes
import time
from pathlib import Path
from typing import Any, Dict, Optional
from sarvamai import SarvamAI


POD_EXTRACTION_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "consignee_name": {
            "type": "string",
            "description": "Name of the consignee or customer recipient printed on the delivery slip"
        },
        "awb_number": {
            "type": "string",
            "description": "Air waybill number, order number, or tracking ID"
        },
        "delivery_address": {
            "type": "string",
            "description": "Destination delivery address on the proof of delivery slip"
        },
        "signature_present": {
            "type": "boolean",
            "description": "True if a handwritten signature or stamp is physically present in the recipient signature section, false otherwise"
        },
        "delivery_date": {
            "type": "string",
            "description": "Date printed or written on the delivery document"
        }
    }
})


class DocumentParser:
    """Parses paper Proof-of-Delivery documents using Sarvam Vision 1.5 Document AI."""

    def __init__(self, client: SarvamAI):
        self.client = client

    def parse_pod_document(
        self,
        file_path: str,
        timeout_seconds: int = 60,
        poll_interval: float = 2.0,
    ) -> Dict[str, Any]:
        """Upload and extract structured fields from a paper POD document.

        Args:
            file_path: Path to PNG, JPG, or PDF proof-of-delivery document.
            timeout_seconds: Maximum seconds to wait for async job completion.
            poll_interval: Seconds between status polls.

        Returns:
            Dict containing parsed fields (consignee_name, signature_present, awb_number, etc.).
        """
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Document file not found: {path}")

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            if path.suffix.lower() in [".jpg", ".jpeg"]:
                mime_type = "image/jpeg"
            elif path.suffix.lower() == ".png":
                mime_type = "image/png"
            elif path.suffix.lower() == ".pdf":
                mime_type = "application/pdf"
            else:
                mime_type = "application/octet-stream"

        with open(path, "rb") as f:
            file_payload = [(path.name, f.read(), mime_type)]

        # Start Document AI extraction job
        job_response = self.client.doc_ai.extract(
            file=file_payload,
            schema=POD_EXTRACTION_SCHEMA,
            language="en-IN",
            output_format="json"
        )

        job_id = job_response.job_id
        start_time = time.time()

        # Poll until job completes
        while time.time() - start_time < timeout_seconds:
            status_response = self.client.doc_ai.get_status(job_id=job_id)
            current_status = getattr(status_response, "status", None)

            if current_status in ["completed", "partially_completed"]:
                results = self.client.doc_ai.get_results(job_id=job_id)
                extracted_data = getattr(results, "result", {}) or {}
                if hasattr(extracted_data, "model_dump"):
                    extracted_data = extracted_data.model_dump()
                elif hasattr(extracted_data, "dict"):
                    extracted_data = extracted_data.dict()

                annotations_data = getattr(results, "annotations", None)
                if hasattr(annotations_data, "model_dump"):
                    annotations_data = annotations_data.model_dump()
                elif hasattr(annotations_data, "dict"):
                    annotations_data = annotations_data.dict()

                return {
                    "job_id": job_id,
                    "status": current_status,
                    "fields": extracted_data,
                    "annotations": annotations_data,
                }
            elif current_status in ["failed", "rejected"]:
                raise RuntimeError(
                    f"Sarvam Document AI job {job_id} failed with status: {current_status}"
                )

            time.sleep(poll_interval)

        raise TimeoutError(
            f"Sarvam Document AI job {job_id} timed out after {timeout_seconds}s"
        )
