import pytest
from app.services.subtitle_service import SubtitleService

def test_parse_text():
    service = SubtitleService(None)
    text = "今天我们来学习Python。首先安装环境！然后开始编程？"
    segments = service.parse_text(text)
    assert len(segments) == 3
    assert segments[0]["content"] == "今天我们来学习Python。"
    assert segments[1]["content"] == "首先安装环境！"

def test_extract_keywords():
    service = SubtitleService(None)
    text = "今天我们来学习Python编程基础"
    keywords = service.extract_keywords(text)
    assert "Python" in keywords
    assert "编程" in keywords or "学习" in keywords

def test_parse_multiline():
    service = SubtitleService(None)
    text = """第一行字幕
第二行字幕
第三行字幕"""
    segments = service.parse_text(text)
    assert len(segments) == 3