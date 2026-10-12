import argparse
import sys
from pathlib import Path
from vpod.pipeline import VoicePODPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Sarvam AI Voice Proof-of-Delivery (vPOD) Verification Pipeline"
    )
    parser.add_argument(
        "--document",
        "-d",
        type=str,
        help="Path to paper POD image (PNG/JPG) or PDF document",
    )
    parser.add_argument(
        "--audio",
        "-a",
        type=str,
        help="Path to recipient voice confirmation audio (WAV/MP3/M4A)",
    )
    parser.add_argument(
        "--awb",
        type=str,
        default="AWB-982347102",
        help="Expected AWB / tracking number for cross-referencing",
    )
    parser.add_argument(
        "--demo",
        choices=["clean", "proxy"],
        default="clean",
        help="Run built-in demo scenario: 'clean' (verified delivery) or 'proxy' (neighbor exception)",
    )

    args = parser.parse_args()

    pipeline = VoicePODPipeline()

    if args.document and args.audio:
        doc_path = args.document
        audio_path = args.audio
        print(f"\n[vPOD] Running verification on custom input files:")
        print(f"  Document: {doc_path}")
        print(f"  Audio:    {audio_path}")
    else:
        # Use built-in test fixtures
        sample_dir = Path(__file__).parent / "sample_data"
        doc_path = str(sample_dir / "sample_pod.pdf")
        if args.demo == "proxy":
            audio_path = str(sample_dir / "sample_proxy_exception.wav")
            print(f"\n[vPOD Demo] Running Scenario: Proxy Delivery Exception (Neighbor)")
        else:
            audio_path = str(sample_dir / "sample_clean_confirmation.wav")
            print(f"\n[vPOD Demo] Running Scenario: Clean Verified Delivery (Named Consignee)")

    order_meta = {
        "expected_awb": args.awb,
        "delivery_agent_id": "AGENT-DEL-104",
        "timestamp": "2026-10-12T14:40:00+05:30",
    }

    try:
        result = pipeline.verify(
            document_path=doc_path,
            audio_path=audio_path,
            order_metadata=order_meta,
        )
        print("\n" + pipeline.format_report(result))
    except Exception as e:
        print(f"\n❌ Error during pipeline execution: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
