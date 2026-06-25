import json

from media_pipeline.analyzers import MockAnalyzer, infer_media_kind
from media_pipeline.config import AppConfig
from media_pipeline.delivery import LocalCallbackCapturePublisher
from media_pipeline.function_app import process_blob_created_event
from media_pipeline.models import MediaKind, PipelineInput
from media_pipeline.pipeline import PipelineRunner
from media_pipeline.storage import LocalJsonStore


def test_infer_media_kind_pdf():
    assert infer_media_kind("invoice.pdf", "application/pdf") == MediaKind.DOCUMENT


def test_pipeline_routes_invoice_to_finance(tmp_path):
    runner = PipelineRunner(
        analyzer=MockAnalyzer(),
        store=LocalJsonStore(tmp_path),
        publisher=LocalCallbackCapturePublisher(tmp_path),
    )
    pipeline_input = PipelineInput(
        source_uri="file:///tmp/invoice.pdf",
        filename="invoice.pdf",
        mime_type="application/pdf",
        media_kind=MediaKind.DOCUMENT,
    )

    result, delivery = runner.run(pipeline_input)

    assert result.routed_output.bucket == "finance-documents"
    assert result.routed_output.normalized_type == "financial_document"
    assert "normalized_output" in result.exported_files
    assert delivery.status == "captured"


def test_process_blob_event_end_to_end(tmp_path):
    payload = {
        "source_uri": "https://example.blob.core.windows.net/incoming/invoice.pdf?sig=demo",
        "filename": "invoice.pdf",
        "mime_type": "application/pdf",
        "customer_id": "contoso",
        "metadata": {"source": "blob"},
    }

    output = process_blob_created_event(
        payload,
        config=AppConfig(
            analyzer_mode="mock",
            output_dir=str(tmp_path),
        ),
    )

    assert output["result"]["routed_output"]["bucket"] == "finance-documents"
    assert output["delivery"]["status"] == "captured"
    callback_path = tmp_path / output["result"]["request_id"] / "callback-payload.json"
    assert callback_path.exists()
    json.loads(callback_path.read_text(encoding="utf-8"))
