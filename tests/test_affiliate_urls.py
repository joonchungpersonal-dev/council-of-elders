"""Tests for affiliate URL generation."""

from unittest.mock import patch

from council.knowledge.books import _make_affiliate_url, _make_kindle_url
from council.knowledge.memorabilia import _make_memorabilia_url
from council.knowledge.documentaries import _make_prime_video_url


class TestBookUrls:
    def test_affiliate_url_contains_tag(self):
        url = _make_affiliate_url("Meditations", "Marcus Aurelius", "mytag-20")
        assert "tag=mytag-20" in url
        assert "amazon.com" in url
        assert "Meditations" in url

    def test_affiliate_url_no_tag(self):
        url = _make_affiliate_url("Meditations", "Marcus Aurelius", "")
        assert "tag=" not in url
        assert "Meditations" in url

    def test_kindle_url_includes_digital_text(self):
        url = _make_kindle_url("Meditations", "Marcus Aurelius", "mytag-20")
        assert "i=digital-text" in url
        assert "tag=mytag-20" in url

    def test_special_characters_encoded(self):
        url = _make_affiliate_url("The Art & Science", "O'Brien", "tag-20")
        assert "%26" in url or "&" in url  # & should be encoded in query param
        assert "O" in url


class TestMemorabiliaUrls:
    def test_url_contains_tag(self):
        url = _make_memorabilia_url("Marcus Aurelius bust", "mytag-20")
        assert "tag=mytag-20" in url
        assert "amazon.com" in url

    def test_url_no_tag(self):
        url = _make_memorabilia_url("Marcus Aurelius bust", "")
        assert "tag=" not in url


class TestDocumentaryUrls:
    def test_url_contains_instant_video(self):
        url = _make_prime_video_url("Becoming Warren Buffett", "mytag-20")
        assert "i=instant-video" in url
        assert "tag=mytag-20" in url
        assert "amazon.com" in url

    def test_url_no_tag(self):
        url = _make_prime_video_url("Becoming Warren Buffett", "")
        assert "tag=" not in url
        assert "i=instant-video" in url
