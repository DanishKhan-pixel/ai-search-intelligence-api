from __future__ import annotations


def calculate_opportunity_score(volume: int, difficulty: int, domain_visible: bool) -> float:
    volume = max(int(volume or 0), 0)
    difficulty = min(max(int(difficulty or 0), 0), 100)

    volume_score = min(volume / 2000.0, 1.0)
    difficulty_score = 1.0 - (difficulty / 100.0)
    visibility_score = 1.0 if not domain_visible else 0.3

    score = 0.5 * volume_score + 0.3 * difficulty_score + 0.2 * visibility_score
    return round(min(max(score, 0.0), 1.0), 2)

