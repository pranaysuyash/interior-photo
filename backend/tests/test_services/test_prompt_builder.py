"""
Tests for PromptBuilder service

Tests cover:
- Prompt generation from vibes
- Color palette integration
- Custom description handling
- Negative prompt generation
"""

import pytest
from app.services.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Test PromptBuilder service"""

    def test_build_prompt_modern_neutral(self):
        """Test prompt building for modern vibe with neutral colors"""
        prompt, negative = PromptBuilder.build_prompt("modern", "neutral", None)

        assert "modern" in prompt.lower() or "contemporary" in prompt.lower()
        assert "neutral" in prompt.lower() or "beige" in prompt.lower()
        assert len(prompt) > 0
        assert len(negative) > 0

    def test_build_prompt_with_description(self):
        """Test prompt building with custom description"""
        description = "Add more plants and natural light"
        prompt, negative = PromptBuilder.build_prompt(
            "scandinavian", "earthy", description
        )

        assert description.lower() in prompt.lower()
        assert "scandinavian" in prompt.lower() or "nordic" in prompt.lower()

    def test_build_prompt_all_vibes(self):
        """Test prompt building for all available vibes"""
        vibes = [
            "modern", "minimalist", "cozy", "industrial",
            "bohemian", "scandinavian", "luxurious", "rustic"
        ]

        for vibe in vibes:
            prompt, negative = PromptBuilder.build_prompt(vibe, "neutral", None)
            assert len(prompt) > 0
            assert len(negative) > 0
            assert isinstance(prompt, str)
            assert isinstance(negative, str)

    def test_build_prompt_all_colors(self):
        """Test prompt building for all color palettes"""
        colors = ["neutral", "warm", "cool", "earthy", "pastel", "bold"]

        for color in colors:
            prompt, negative = PromptBuilder.build_prompt("modern", color, None)
            assert len(prompt) > 0
            assert len(negative) > 0

    def test_build_prompt_invalid_vibe(self):
        """Test prompt building with invalid vibe falls back gracefully"""
        prompt, negative = PromptBuilder.build_prompt("invalid_vibe", "neutral", None)

        # Should still generate a prompt (fallback)
        assert len(prompt) > 0
        assert len(negative) > 0

    def test_negative_prompt_contains_unwanted_elements(self):
        """Test that negative prompt contains unwanted elements"""
        _, negative = PromptBuilder.build_prompt("modern", "neutral", None)

        unwanted_keywords = ["blurry", "distorted", "ugly", "poor quality"]
        assert any(keyword in negative.lower() for keyword in unwanted_keywords)
