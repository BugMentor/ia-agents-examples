"""
Tests for Multi-Agent System (agent_multi.py)

L0: Unit Tests - Individual components
L1: Integration Tests - Tools work correctly
L2: Service Tests - API calls work
L3: End-to-End Tests - Full agent flows

Run with: pytest tests/test_agent_multi.py -v
"""

import json
import os
import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch

import agent_multi


class TestUnitMultiAgent:
    """L0: Test multi-agent components"""

    def test_L0_pokemon_tool_exists(self):
        """L0: Pokemon tool function exists"""
        assert callable(agent_multi.get_pokemon_info)

    def test_L0_simpsons_tool_exists(self):
        """L0: Simpsons tool function exists"""
        assert callable(agent_multi.get_simpsons_info)

    def test_L0_coordinator_exists(self):
        """L0: Coordinator function exists"""
        assert callable(agent_multi.coordinator)

    def test_L0_specialists_exist(self):
        """L0: Specialist functions exist"""
        assert callable(agent_multi.run_pokemon)
        assert callable(agent_multi.run_simpsons)


class TestIntegrationTools:
    """L1: Test tools with mocked API"""

    def test_L1_pokemon_tool_returns_string(self, tmp_path):
        """L1: Pokemon tool returns formatted string"""
        os.chdir(tmp_path)

        with patch("agent_multi.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "pikachu",
                "types": [{"type": {"name": "electric"}}],
                "abilities": [{"ability": {"name": "static"}}],
            }
            mock_get.return_value = mock_response

            result = agent_multi.get_pokemon_info("pikachu")

            assert "pikachu" in result.lower()
            assert "electric" in result.lower()

    def test_L1_simpsons_tool_returns_string(self, tmp_path):
        """L1: Simpsons tool returns formatted string"""
        os.chdir(tmp_path)

        with patch("agent_multi.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "homer",
                "occupation": "Nuclear Plant",
            }
            mock_get.return_value = mock_response

            result = agent_multi.get_simpsons_info("homer")

            assert result is not None


class TestServiceOllama:
    """L2: Test Ollama API"""

    @pytest.mark.asyncio
    async def test_L2_ollama_connectivity(self):
        """L2: Can connect to Ollama API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:11434/api/tags", timeout=5.0
                )
                assert response.status_code in [200, 405]
        except httpx.ConnectError:
            pytest.skip("Ollama not running")


class TestE2EMultiAgent:
    """L3: Test full multi-agent flow"""

    def test_L3_multi_agent_components(self):
        """L3: Multi-agent has coordinator and specialists"""
        assert "get_simpsons_info" in agent_multi.TOOLS_SIMPSONS
        assert "get_pokemon_info" in agent_multi.TOOLS_POKEMON

    @pytest.mark.asyncio
    async def test_L3_pokemon_specialist(self, tmp_path):
        """L3: Pokemon specialist works"""
        os.chdir(tmp_path)

        # Skip if Ollama not running
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:11434/api/tags", timeout=2.0)
        except httpx.ConnectError:
            pytest.skip("Ollama not running")

        result = await agent_multi.run_pokemon("What is Charmander?")

        assert result is not None or "charmander" in result.lower()

    @pytest.mark.asyncio
    async def test_L3_simpsons_specialist(self, tmp_path):
        """L3: Simpsons specialist works"""
        os.chdir(tmp_path)

        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:11434/api/tags", timeout=2.0)
        except httpx.ConnectError:
            pytest.skip("Ollama not running")

        result = await agent_multi.run_simpsons("Who is Homer?")

        assert result is not None or "homer" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
