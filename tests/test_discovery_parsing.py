"""Tests for LLM discovery output parsing resilience."""

from unittest.mock import patch

from council.knowledge.books import discover_books
from council.knowledge.memorabilia import discover_memorabilia
from council.knowledge.documentaries import discover_documentaries


def _mock_chat(response_text):
    """Create a mock chat function that yields the given text."""
    def fake_chat(messages, stream=False):
        yield response_text
    return fake_chat


class TestBookParsing:
    @patch("council.knowledge.books.get_config_value", return_value="test-tag")
    def test_standard_format(self, mock_config):
        with patch("council.knowledge.books.chat", side_effect=_mock_chat(
            "BY: Meditations | Marcus Aurelius\n"
            "ABOUT: How to Think Like a Roman Emperor | Donald Robertson"
        )):
            books = discover_books("Marcus Aurelius")
            assert len(books) == 2
            assert books[0]["type"] == "by"
            assert books[0]["title"] == "Meditations"
            assert books[1]["type"] == "about"

    @patch("council.knowledge.books.get_config_value", return_value="")
    def test_fallback_by_separator(self, mock_config):
        with patch("council.knowledge.books.chat", side_effect=_mock_chat(
            "BY: Meditations by Marcus Aurelius"
        )):
            books = discover_books("Marcus Aurelius")
            assert len(books) == 1
            assert books[0]["title"] == "Meditations"

    @patch("council.knowledge.books.get_config_value", return_value="")
    def test_dash_separator_fallback(self, mock_config):
        with patch("council.knowledge.books.chat", side_effect=_mock_chat(
            "BY: Meditations - Marcus Aurelius"
        )):
            books = discover_books("Marcus Aurelius")
            assert len(books) == 1
            assert books[0]["title"] == "Meditations"

    @patch("council.knowledge.books.get_config_value", return_value="")
    def test_garbage_input_returns_empty(self, mock_config):
        with patch("council.knowledge.books.chat", side_effect=_mock_chat(
            "Here are some great books I recommend!\nEnjoy reading them."
        )):
            books = discover_books("Marcus Aurelius")
            assert len(books) == 0

    @patch("council.knowledge.books.get_config_value", return_value="")
    def test_asterisks_and_quotes_stripped(self, mock_config):
        with patch("council.knowledge.books.chat", side_effect=_mock_chat(
            'BY: *Meditations* | *Marcus Aurelius*'
        )):
            books = discover_books("Marcus Aurelius")
            assert len(books) == 1
            assert books[0]["title"] == "Meditations"
            assert books[0]["author"] == "Marcus Aurelius"


class TestMemorabiliaParsing:
    @patch("council.knowledge.memorabilia.get_config_value", return_value="test-tag")
    def test_standard_format(self, mock_config):
        with patch("council.knowledge.memorabilia.chat", side_effect=_mock_chat(
            "bust: Marcus Aurelius Bronze Bust | Detailed replica of the Roman Emperor\n"
            "coin: Roman Empire Aureus Coin Replica | Gold-plated commemorative coin"
        )):
            items = discover_memorabilia("Marcus Aurelius")
            assert len(items) == 2
            assert items[0]["category"] == "bust"
            assert items[1]["category"] == "coin"
            assert "test-tag" in items[0]["affiliate_url"]

    @patch("council.knowledge.memorabilia.get_config_value", return_value="")
    def test_dash_separator_fallback(self, mock_config):
        with patch("council.knowledge.memorabilia.chat", side_effect=_mock_chat(
            "bust: Marcus Aurelius Bust - A beautiful bronze replica"
        )):
            items = discover_memorabilia("Marcus Aurelius")
            assert len(items) == 1

    @patch("council.knowledge.memorabilia.get_config_value", return_value="")
    def test_invalid_category_skipped(self, mock_config):
        with patch("council.knowledge.memorabilia.chat", side_effect=_mock_chat(
            "book: Some Book | Not a valid memorabilia category"
        )):
            items = discover_memorabilia("Marcus Aurelius")
            assert len(items) == 0


class TestDocumentaryParsing:
    @patch("council.knowledge.documentaries.get_config_value", return_value="test-tag")
    def test_standard_format(self, mock_config):
        with patch("council.knowledge.documentaries.chat", side_effect=_mock_chat(
            "documentary: Becoming Warren Buffett | HBO documentary about the Oracle of Omaha"
        )):
            items = discover_documentaries("Warren Buffett")
            assert len(items) == 1
            assert items[0]["type"] == "documentary"
            assert items[0]["title"] == "Becoming Warren Buffett"
            assert "test-tag" in items[0]["amazon_url"]
            assert "instant-video" in items[0]["amazon_url"]

    @patch("council.knowledge.documentaries.get_config_value", return_value="")
    def test_dash_separator_fallback(self, mock_config):
        with patch("council.knowledge.documentaries.chat", side_effect=_mock_chat(
            "lecture: The Psychology of Human Misjudgment - Charlie Munger's famous lecture"
        )):
            items = discover_documentaries("Charlie Munger")
            assert len(items) == 1
            assert items[0]["type"] == "lecture"

    @patch("council.knowledge.documentaries.get_config_value", return_value="")
    def test_invalid_type_skipped(self, mock_config):
        with patch("council.knowledge.documentaries.chat", side_effect=_mock_chat(
            "movie: Some Movie | Not a valid documentary type"
        )):
            items = discover_documentaries("Charlie Munger")
            assert len(items) == 0
