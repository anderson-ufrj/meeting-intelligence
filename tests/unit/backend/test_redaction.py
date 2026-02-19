"""Tests for PII redaction module (Phase 2)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.redaction import PIIRedactor, RedactionResult, simple_redact


@pytest.fixture
def mock_presidio():
    """Patch Presidio analyzer and anonymizer engines."""
    with patch("backend.redaction.AnalyzerEngine") as mock_analyzer_cls, \
         patch("backend.redaction.AnonymizerEngine") as mock_anonymizer_cls:
        mock_analyzer = MagicMock()
        mock_anonymizer = MagicMock()
        mock_analyzer_cls.return_value = mock_analyzer
        mock_anonymizer_cls.return_value = mock_anonymizer
        yield mock_analyzer, mock_anonymizer


class TestPIIRedactorInit:
    def test_default_language(self, mock_presidio):
        redactor = PIIRedactor()
        assert redactor.language == "en"

    def test_custom_language(self, mock_presidio):
        redactor = PIIRedactor(language="es")
        assert redactor.language == "es"


class TestDefaultEntities:
    def test_has_all_8_entities(self):
        assert len(PIIRedactor.DEFAULT_ENTITIES) == 8

    def test_includes_key_entities(self):
        entities = PIIRedactor.DEFAULT_ENTITIES
        assert "PERSON" in entities
        assert "PHONE_NUMBER" in entities
        assert "EMAIL_ADDRESS" in entities
        assert "CREDIT_CARD" in entities
        assert "LOCATION" in entities


class TestRedact:
    def _make_analyzer_result(self, entity_type, start, end, score=0.85):
        result = MagicMock()
        result.entity_type = entity_type
        result.start = start
        result.end = end
        result.score = score
        return result

    def test_detects_email(self, mock_presidio):
        mock_analyzer, mock_anonymizer = mock_presidio
        email_result = self._make_analyzer_result("EMAIL_ADDRESS", 8, 24)
        mock_analyzer.analyze.return_value = [email_result]

        anonymized = MagicMock()
        anonymized.text = "Contact <EMAIL_ADDRESS> for info."
        mock_anonymizer.anonymize.return_value = anonymized

        redactor = PIIRedactor()
        result = redactor.redact("Contact john@example.com for info.")

        assert result.redacted_text == "Contact <EMAIL_ADDRESS> for info."
        assert result.redaction_count == 1
        assert result.entities_found[0]["type"] == "EMAIL_ADDRESS"

    def test_detects_phone(self, mock_presidio):
        mock_analyzer, mock_anonymizer = mock_presidio
        phone_result = self._make_analyzer_result("PHONE_NUMBER", 8, 22)
        mock_analyzer.analyze.return_value = [phone_result]

        anonymized = MagicMock()
        anonymized.text = "Call me <PHONE_NUMBER> tomorrow."
        mock_anonymizer.anonymize.return_value = anonymized

        redactor = PIIRedactor()
        result = redactor.redact("Call me 555-123-4567 tomorrow.")

        assert "<PHONE_NUMBER>" in result.redacted_text
        assert result.redaction_count == 1

    def test_no_entities_returns_original(self, mock_presidio):
        mock_analyzer, mock_anonymizer = mock_presidio
        mock_analyzer.analyze.return_value = []

        redactor = PIIRedactor()
        result = redactor.redact("This text has no PII.")

        assert result.redacted_text == "This text has no PII."
        assert result.redaction_count == 0
        assert result.entities_found == []
        mock_anonymizer.anonymize.assert_not_called()

    def test_multiple_entities(self, mock_presidio):
        mock_analyzer, mock_anonymizer = mock_presidio
        results = [
            self._make_analyzer_result("EMAIL_ADDRESS", 0, 16),
            self._make_analyzer_result("PHONE_NUMBER", 20, 34),
        ]
        mock_analyzer.analyze.return_value = results

        anonymized = MagicMock()
        anonymized.text = "<EMAIL_ADDRESS> or <PHONE_NUMBER>"
        mock_anonymizer.anonymize.return_value = anonymized

        redactor = PIIRedactor()
        result = redactor.redact("john@example.com or 555-123-4567")

        assert result.redaction_count == 2
        assert len(result.entities_found) == 2

    def test_custom_entities(self, mock_presidio):
        mock_analyzer, mock_anonymizer = mock_presidio
        mock_analyzer.analyze.return_value = []

        redactor = PIIRedactor()
        redactor.redact("Test", entities=["CREDIT_CARD"])

        call_kwargs = mock_analyzer.analyze.call_args
        assert call_kwargs.kwargs["entities"] == ["CREDIT_CARD"]


class TestRedactTranscript:
    def test_preserves_speakers(self, mock_presidio):
        mock_analyzer, mock_anonymizer = mock_presidio
        # Simulate that first redact replaces speaker names
        person_result = MagicMock()
        person_result.entity_type = "PERSON"
        person_result.start = 10
        person_result.end = 25
        person_result.score = 0.9
        mock_analyzer.analyze.return_value = [person_result]

        anonymized = MagicMock()
        anonymized.text = "[00:00:15] <PERSON>: Hello everyone"
        mock_anonymizer.anonymize.return_value = anonymized

        redactor = PIIRedactor()
        result = redactor.redact_transcript(
            "[00:00:15] Alice Johnson: Hello everyone",
            preserve_speakers=["Alice Johnson"],
        )

        assert isinstance(result, RedactionResult)

    def test_without_preservation(self, mock_presidio):
        mock_analyzer, mock_anonymizer = mock_presidio
        mock_analyzer.analyze.return_value = []

        redactor = PIIRedactor()
        result = redactor.redact_transcript("Some transcript text")

        assert isinstance(result, RedactionResult)
        assert result.redacted_text == "Some transcript text"


class TestAuditLogEntry:
    def test_format(self, mock_presidio):
        redactor = PIIRedactor()
        redaction_result = RedactionResult(
            redacted_text="<EMAIL_ADDRESS>",
            entities_found=[{"type": "EMAIL_ADDRESS", "start": 0, "end": 16, "score": 0.9}],
            redaction_count=1,
        )

        entry = redactor.get_audit_log_entry("meeting_123", redaction_result, user="admin")

        assert "timestamp" in entry
        assert entry["meeting_id"] == "meeting_123"
        assert entry["action"] == "pii_redaction"
        assert entry["user"] == "admin"
        assert entry["entities_redacted"] == 1
        assert "EMAIL_ADDRESS" in entry["entity_types"]

    def test_default_user_is_system(self, mock_presidio):
        redactor = PIIRedactor()
        redaction_result = RedactionResult(redacted_text="x", entities_found=[], redaction_count=0)
        entry = redactor.get_audit_log_entry("m1", redaction_result)
        assert entry["user"] == "system"


class TestSimpleRedact:
    def test_email(self):
        result = simple_redact("Contact john@example.com please")
        assert "<EMAIL>" in result
        assert "john@example.com" not in result

    def test_phone(self):
        result = simple_redact("Call 555-123-4567 now")
        assert "<PHONE>" in result
        assert "555-123-4567" not in result

    def test_ssn(self):
        result = simple_redact("SSN is 123-45-6789")
        assert "<SSN>" in result
        assert "123-45-6789" not in result

    def test_no_pii_unchanged(self):
        text = "This is a normal sentence."
        assert simple_redact(text) == text
