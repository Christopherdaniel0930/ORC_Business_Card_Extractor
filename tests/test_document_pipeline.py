from app.business_card.models.business_card_model import BusinessCardData
from app.common import document_pipeline


class FakeClient:
    def extract(self, prompt):
        return '{"name":"Ada Lovelace","designation":"Engineer"}'


def test_business_card_pipeline_uses_one_ocr_pass_and_injected_client(monkeypatch):
    rows = [{"text": "Ada Lovelace"}, {"text": "Engineer"}]
    calls = []
    monkeypatch.setattr(document_pipeline, "read_ocr_rows", lambda path: calls.append(path) or rows)
    result = document_pipeline.process_document("card.png", llm_client=FakeClient())
    assert calls == ["card.png"]
    assert result["document_type"] == "business_card"
    assert isinstance(result["data"], BusinessCardData)
    assert result["data"].name == "Ada Lovelace"


def test_empty_ocr_fails_before_extraction(monkeypatch):
    monkeypatch.setattr(document_pipeline, "read_ocr_rows", lambda path: [])
    try:
        document_pipeline.process_document("blank.png", llm_client=FakeClient())
    except RuntimeError as exc:
        assert str(exc) == "OCR returned no text"
    else:
        raise AssertionError("empty OCR should fail")
