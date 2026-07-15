import pytest
from app.services.matching_service import MatchingService

def test_keyword_match():
    service = MatchingService(None)
    score = service.keyword_match(["Python", "编程"], ["Python", "代码"])
    assert score == 1/3  # 1个共同关键词 / 3个总关键词

def test_keyword_match_empty():
    service = MatchingService(None)
    assert service.keyword_match([], ["Python"]) == 0.0
    assert service.keyword_match(["Python"], []) == 0.0

def test_generate_reason():
    service = MatchingService(None)
    reason = service.generate_reason(["Python", "编程"], 0.85)
    assert "关键词匹配: Python, 编程" in reason
    assert "语义高度相关" in reason