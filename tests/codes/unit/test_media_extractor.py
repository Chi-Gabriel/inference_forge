from app.platform.media.extractor import is_extractor_url


def test_extractor_url_matches_allowed_provider_hosts() -> None:
    allowed = ["youtube.com", "youtu.be", "tiktok.com", "facebook.com", "fb.watch"]

    assert is_extractor_url("https://www.youtube.com/watch?v=abc", allowed)
    assert is_extractor_url("https://youtu.be/abc", allowed)
    assert is_extractor_url("https://www.tiktok.com/@x/video/1", allowed)
    assert is_extractor_url("https://fb.watch/abc", allowed)


def test_extractor_url_rejects_unlisted_hosts() -> None:
    allowed = ["youtube.com"]

    assert not is_extractor_url("https://example.com/video.mp4", allowed)
    assert not is_extractor_url("https://notyoutube.com/watch?v=abc", allowed)
