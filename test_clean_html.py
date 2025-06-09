from prompt_gemini import clean_html_for_prompt, gemini_generation
import os
import pytest


def test_removes_base64_and_scripts():
    html = """
    <html><head><script>var x=1;</script></head>
    <body>
    <img src="data:image/png;base64,AAAABBBBCCCC" />
    <div>Content</div>
    </body></html>
    """
    cleaned = clean_html_for_prompt(html)
    assert "script" not in cleaned
    assert "base64" not in cleaned
    assert "AAAABBBBCCCC" not in cleaned


def test_remove_multimedia_tags():
    html = """
    <html><body>
    <video><source src='movie.mp4'></source></video>
    <canvas>ignored</canvas>
    <svg><circle /></svg>
    <div>Keep</div>
    </body></html>
    """
    cleaned = clean_html_for_prompt(html)
    assert "<video" not in cleaned
    assert "<canvas" not in cleaned
    assert "<svg" not in cleaned


def test_remove_comments_and_whitespace():
    html = """
    <html>
    <!-- remove me -->
    <body>  Text     </body>
    </html>
    """
    cleaned = clean_html_for_prompt(html)
    assert "remove me" not in cleaned
    # whitespace collapsed to single space
    assert "  " not in cleaned.strip()


def test_gemini_generation_requires_key():
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    with pytest.raises(RuntimeError):
        gemini_generation("test")
