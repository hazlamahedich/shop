"""Tests for WidgetTheme schema validation.

Story 5.5: Theme Customization System
Validates all 11 theme fields with ranges and sanitization.
"""

import pytest
from pydantic import ValidationError

from app.schemas.widget import WidgetTheme


class TestWidgetThemeValidation:
    def test_default_theme_values(self):
        theme = WidgetTheme()
        assert theme.primary_color == "#6366f1"
        assert theme.background_color == "#ffffff"
        assert theme.text_color == "#1f2937"
        assert theme.bot_bubble_color == "#f3f4f6"
        assert theme.user_bubble_color == "#6366f1"
        assert theme.position == "bottom-right"
        assert theme.border_radius == 16
        assert theme.width == 380
        assert theme.height == 600
        assert theme.font_family == "Inter, sans-serif"
        assert theme.font_size == 14

    def test_all_11_fields_accepted(self):
        theme = WidgetTheme(
            primary_color="#ff0000",
            background_color="#000000",
            text_color="#ffffff",
            bot_bubble_color="#111111",
            user_bubble_color="#222222",
            position="bottom-left",
            border_radius=24,
            width=600,
            height=900,
            font_family="Arial, sans-serif",
            font_size=20,
        )
        assert theme.primary_color == "#ff0000"
        assert theme.background_color == "#000000"
        assert theme.text_color == "#ffffff"
        assert theme.bot_bubble_color == "#111111"
        assert theme.user_bubble_color == "#222222"
        assert theme.position == "bottom-left"
        assert theme.border_radius == 24
        assert theme.width == 600
        assert theme.height == 900
        assert theme.font_family == "Arial, sans-serif"
        assert theme.font_size == 20


class TestColorValidation:
    def test_valid_hex_colors(self):
        theme = WidgetTheme(
            primary_color="#6366f1",
            background_color="#ffffff",
            text_color="#1f2937",
            bot_bubble_color="#f3f4f6",
            user_bubble_color="#6366f1",
        )
        assert theme.primary_color == "#6366f1"

    def test_invalid_color_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(primary_color="red")
        assert "primary_color" in str(exc_info.value)

    def test_invalid_hex_short_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(primary_color="#fff")
        assert "primary_color" in str(exc_info.value)

    def test_invalid_hex_letters_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(primary_color="#gggggg")
        assert "primary_color" in str(exc_info.value)


class TestBorderRadiusValidation:
    def test_border_radius_min_0(self):
        theme = WidgetTheme(border_radius=0)
        assert theme.border_radius == 0

    def test_border_radius_max_24(self):
        theme = WidgetTheme(border_radius=24)
        assert theme.border_radius == 24

    def test_border_radius_25_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(border_radius=25)
        assert "border_radius" in str(exc_info.value)

    def test_border_radius_negative_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(border_radius=-1)
        assert "border_radius" in str(exc_info.value)


class TestWidthHeightValidation:
    def test_width_min_280(self):
        theme = WidgetTheme(width=280)
        assert theme.width == 280

    def test_width_max_600(self):
        theme = WidgetTheme(width=600)
        assert theme.width == 600

    def test_width_below_min_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(width=279)
        assert "width" in str(exc_info.value)

    def test_width_above_max_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(width=601)
        assert "width" in str(exc_info.value)

    def test_height_min_400(self):
        theme = WidgetTheme(height=400)
        assert theme.height == 400

    def test_height_max_900(self):
        theme = WidgetTheme(height=900)
        assert theme.height == 900

    def test_height_below_min_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(height=399)
        assert "height" in str(exc_info.value)

    def test_height_above_max_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(height=901)
        assert "height" in str(exc_info.value)


class TestPositionValidation:
    def test_position_bottom_right(self):
        theme = WidgetTheme(position="bottom-right")
        assert theme.position == "bottom-right"

    def test_position_bottom_left(self):
        theme = WidgetTheme(position="bottom-left")
        assert theme.position == "bottom-left"

    def test_position_top_right_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(position="top-right")
        assert "position" in str(exc_info.value)

    def test_position_invalid_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(position="center")
        assert "position" in str(exc_info.value)


class TestFontSizeValidation:
    def test_font_size_min_12(self):
        theme = WidgetTheme(font_size=12)
        assert theme.font_size == 12

    def test_font_size_max_20(self):
        theme = WidgetTheme(font_size=20)
        assert theme.font_size == 20

    def test_font_size_below_min_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(font_size=11)
        assert "font_size" in str(exc_info.value)

    def test_font_size_above_max_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            WidgetTheme(font_size=21)
        assert "font_size" in str(exc_info.value)


class TestFontFamilySanitization:
    def test_font_family_sanitize_script_tag(self):
        theme = WidgetTheme(font_family="<script>alert(1)</script>")
        assert "<" not in theme.font_family
        assert ">" not in theme.font_family

    def test_font_family_sanitize_quotes(self):
        theme = WidgetTheme(font_family='Arial"onclick=alert(1)')
        assert '"' not in theme.font_family

    def test_font_family_sanitize_single_quotes(self):
        theme = WidgetTheme(font_family="Arial'onclick=alert(1)")
        assert "'" not in theme.font_family

    def test_font_family_valid_preserved(self):
        theme = WidgetTheme(font_family="Georgia, serif")
        assert theme.font_family == "Georgia, serif"

    def test_font_family_complex_preserved(self):
        theme = WidgetTheme(font_family="'Segoe UI', Roboto, sans-serif")
        assert "'" not in theme.font_family
        assert "Segoe UI" in theme.font_family


class TestCamelCaseAlias:
    def test_aliases_for_all_fields(self):
        theme = WidgetTheme(
            primaryColor="#ff0000",
            backgroundColor="#000000",
            textColor="#ffffff",
            botBubbleColor="#111111",
            userBubbleColor="#222222",
            position="bottom-left",
            borderRadius=20,
            width=500,
            height=700,
            fontFamily="Arial",
            fontSize=16,
        )
        assert theme.primary_color == "#ff0000"
        assert theme.border_radius == 20

    def test_serialization_uses_camel_case(self):
        theme = WidgetTheme(border_radius=20, width=500)
        data = theme.model_dump()
        assert "borderRadius" in data
        assert data["borderRadius"] == 20
        assert "width" in data
        assert data["width"] == 500
