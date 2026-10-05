"""Unit tests for the CertifyMe AI code verifier."""

import pytest

from code_verifier import (
    _generate_mock_analysis,
    get_skill_level,
    verify_code,
)


@pytest.mark.parametrize(
    "score,expected",
    [
        (95, "Expert"),
        (90, "Expert"),
        (89, "Advanced"),
        (75, "Advanced"),
        (74, "Intermediate"),
        (60, "Intermediate"),
        (59, "Beginner"),
        (45, "Beginner"),
        (44, "FAIL - Do not certify"),
        (0, "FAIL - Do not certify"),
    ],
)
def test_get_skill_level_thresholds(score, expected):
    assert get_skill_level(score) == expected


def test_mock_analysis_is_deterministic():
    url = "https://github.com/user/example-repo"
    first = _generate_mock_analysis(url, "Python Backend", 12)
    second = _generate_mock_analysis(url, "Python Backend", 12)
    assert first == second


def test_mock_analysis_structure():
    result = _generate_mock_analysis("https://github.com/user/repo", "React Development", 8)

    assert result["ai_score"] == pytest.approx(
        round(
            result["analysis"]["code_quality"] * 0.30
            + result["analysis"]["complexity"] * 0.25
            + result["analysis"]["best_practices"] * 0.25
            + result["analysis"]["originality"] * 0.20
        )
    )
    assert result["verified"] == (result["ai_score"] >= 45)
    assert result["recommendation"] in ("ISSUE_CERTIFICATE", "REJECT")
    assert len(result["analysis"]["strengths"]) == 2
    assert len(result["analysis"]["weaknesses"]) == 2


def test_mock_analysis_score_bounds():
    for i in range(50):
        url = f"https://github.com/user/repo-{i}"
        result = _generate_mock_analysis(url, "Full Stack Development", 5)
        assert 0 <= result["ai_score"] <= 100
        for key in ("code_quality", "complexity", "best_practices", "originality"):
            assert 0 <= result["analysis"][key] <= 100


def test_verify_code_rejects_when_fetch_fails(monkeypatch):
    def boom(url):
        raise ValueError("Could not fetch repo tree (HTTP 404)")

    monkeypatch.setattr("code_verifier.fetch_github_repo_files", boom)
    result = verify_code("https://github.com/user/nonexistent", "Python Backend")

    assert result["verified"] is False
    assert result["recommendation"] == "REJECT"
    assert result["ai_score"] == 0


def test_verify_code_rejects_empty_repo(monkeypatch):
    monkeypatch.setattr("code_verifier.fetch_github_repo_files", lambda url: {})
    result = verify_code("https://github.com/user/empty-repo", "Python Backend")

    assert result["verified"] is False
    assert result["recommendation"] == "REJECT"
    assert "No source files" in result["analysis"]["error"]


def test_verify_code_demo_mode_falls_back_to_mock(monkeypatch):
    monkeypatch.setattr(
        "code_verifier.fetch_github_repo_files",
        lambda url: {"src/app.py": "print('hello')"},
    )
    result = verify_code("https://github.com/user/repo", "Python Backend")

    # No OPENROUTER_API_KEY in the test environment -> deterministic mock path
    assert result["skill_level"] == get_skill_level(result["ai_score"])
    assert result["verified"] == (result["ai_score"] >= 45)
