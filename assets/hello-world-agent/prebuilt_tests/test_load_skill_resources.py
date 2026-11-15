"""Tests for load_skill_resources.py — skill tool loading."""
# pyright: reportMissingImports=false

import os
import pytest


def _make_skill(tmp_path, folder_name: str, content: str) -> None:
    skill_dir = tmp_path / folder_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


@pytest.mark.structure
class TestValidateAndParseFrontmatter:
    def test_valid_frontmatter_returns_name_and_description(self, add_agent_to_path):
        from load_skill_resources import _validate_and_parse_frontmatter
        name, description = _validate_and_parse_frontmatter("---\nname: my-skill\ndescription: Does something\n---\n# Body")
        assert name == "my-skill"
        assert description == "Does something"

    def test_invalid_frontmatter_missing_opening_fence(self, add_agent_to_path):
        from load_skill_resources import _validate_and_parse_frontmatter
        with pytest.raises(ValueError, match="missing frontmatter opening"):
            _validate_and_parse_frontmatter("name: my-skill\ndescription: foo")

    def test_actual_skills_load_without_error(self, add_agent_to_path):
        import load_skill_resources
        tools = load_skill_resources.get_load_skill_resource_tool()
        assert isinstance(tools, list)


@pytest.mark.structure
class TestLoadPathTraversal:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, add_agent_to_path, monkeypatch):
        import load_skill_resources
        skills_dir = (tmp_path / "skills").resolve()
        _make_skill(skills_dir, "skill1", "---\nname: skill1\ndescription: d\n---\n# Body\nLEGIT")
        self.external = tmp_path / "secret.txt"
        self.external.write_text("SECRET", encoding="utf-8")
        monkeypatch.setattr(load_skill_resources, "_SKILLS_DIR", skills_dir)
        self.skills_dir = skills_dir
        self.load = load_skill_resources._load

    async def test_dot_dot_traversal(self):
        result = await self.load("../secret.txt")
        assert result.startswith("Error:")
        assert "SECRET" not in result

    async def test_absolute_path_injection(self):
        result = await self.load(str(self.external))
        assert result.startswith("Error:")
        assert "SECRET" not in result
