# Voice Proof-of-Delivery (vPOD) with Sarvam AI

An automated delivery verification and exception flagging pipeline powered by Sarvam AI:
1. **Document AI (`Sarvam Vision 1.5`)**: Parses paper POD documents, consignee names, AWB tracking numbers, and checks handwritten signature presence.
2. **Speech-to-Text (`Saaras v4`)**: Captures customer voice confirmations at the doorstep, transcribes regional Indic languages (Hindi, Tamil, etc.), and generates English translations for auditing.
3. **Indic Reasoning (`Sarvam-105B`)**: Cross-examines document fields with the voice transcript to flag delivery exceptions (proxy deliveries, missing signatures, package damages, disputes).

---

## Quickstart

### 1. Requirements & Setup
Make sure your Sarvam API key is configured in `.env`:
```ini
SARVAM_API_KEY=your_key_here
```

### 2. Run Built-in Demos

#### Clean Delivery (Named Consignee)
```bash
python run_vpod.py --demo clean
```

#### Proxy Delivery Exception (Delivered to Neighbor)
```bash
python run_vpod.py --demo proxy
```

---

## Running on Custom Delivery Data

```bash
python run_vpod.py --document path/to/challan.jpg --audio path/to/voice_clip.wav --awb AWB-982347102
```

---

## Python API Usage

```python
from vpod.pipeline import VoicePODPipeline

pipeline = VoicePODPipeline()

result = pipeline.verify(
    document_path="sample_data/sample_pod.pdf",
    audio_path="sample_data/sample_clean_confirmation.wav",
    order_metadata={
        "expected_awb": "AWB-982347102",
        "delivery_agent_id": "AGENT-DEL-104",
    }
)

# Print human-readable report
print(pipeline.format_report(result))

# Or inspect the structured verdict
print(result["verdict"])
```
