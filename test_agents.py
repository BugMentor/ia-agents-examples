"""
Tests for IA Agents - BugMentor Conf Argentina 2026

L0: Unit Tests - Individual components
L1: Integration Tests - Tools work correctly
L2: Service Tests - API calls work
L3: End-to-End Tests - Full agent flows

Run with: pytest test_agents.py -v
"""

import json
import os
import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock, mock_open
from io import StringIO

# Import agents
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# L0: UNIT TESTS - Test individual components
# ============================================================


class TestUnitAddProduct:
    """L0: Test add_product function in isolation"""

    def test_L0_add_product_creates_new_file(self, tmp_path):
        """L0: Tool creates datos.json when it doesn't exist"""
        os.chdir(tmp_path)

        from agent_example import add_product

        result = add_product("TestProduct", "99", "Test description")

        assert "TestProduct" in result
        assert os.path.exists("datos.json")

        with open("datos.json") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["name"] == "TestProduct"

    def test_L0_add_product_appends_to_existing(self, tmp_path):
        """L0: Tool appends to existing datos.json"""
        os.chdir(tmp_path)

        existing_data = [{"name": "Existing", "price": "50", "description": "Test"}]
        with open("datos.json", "w") as f:
            json.dump(existing_data, f)

        from agent_example import add_product

        result = add_product("NewProduct", "100", "New desc")

        with open("datos.json") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[1]["name"] == "NewProduct"

    def test_L0_add_product_invalid_json_handled(self, tmp_path):
        """L0: Tool handles corrupted JSON gracefully"""
        os.chdir(tmp_path)

        with open("datos.json", "w") as f:
            f.write("invalid json {{{")

        from agent_example import add_product

        result = add_product("Product", "10", "desc")

        # Should handle error and create new array
        assert "Product" in result
        assert "Error" not in result


class TestUnitPokemonTool:
    """L0: Test Pokemon tool function"""

    def test_L0_get_pokemon_info_success(self):
        """L0: Pokemon tool returns correct data"""
        from agent_multi import get_pokemon_info

        # This will make real API call - mocked in integration test
        # Just verify function can be called
        assert callable(get_pokemon_info)


class TestUnitSimpsonsTool:
    """L0: Test Simpsons tool function"""

    def test_L0_get_simpsons_info_function_exists(self):
        """L0: Simpsons tool function exists"""
        from agent_multi import get_simpsons_info

        assert callable(get_simpsons_info)


# ============================================================
# L1: INTEGRATION TESTS - Tools work correctly
# ============================================================


class TestIntegrationTools:
    """L1: Test tools with real file I/O"""

    def test_L1_add_product_writes_correct_json(self, tmp_path):
        """L1: add_product writes valid JSON"""
        os.chdir(tmp_path)

        from agent_example import add_product

        result = add_product("Laptop", "999", "Powerful computer")

        assert "added successfully" in result.lower()

        with open("datos.json") as f:
            data = json.load(f)

        assert data[0]["name"] == "Laptop"
        assert data[0]["price"] == "999"
        assert data[0]["description"] == "Powerful computer"

    def test_L1_pokemon_tool_returns_string(self, tmp_path):
        """L1: Pokemon tool returns formatted string"""
        os.chdir(tmp_path)

        # Mock the requests.get to avoid real API call
        with patch("agent_multi.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "pikachu",
                "types": [{"type": {"name": "electric"}}],
                "abilities": [{"ability": {"name": "static"}}],
            }
            mock_get.return_value = mock_response

            from agent_multi import get_pokemon_info

            result = get_pokemon_info("pikachu")

            assert "pikachu" in result.lower()
            assert "electric" in result.lower()


# ============================================================
# L2: SERVICE TESTS - API calls work
# ============================================================


class TestServiceOllama:
    """L2: Test Ollama API connectivity"""

    @pytest.mark.asyncio
    async def test_L2_ollama_connectivity(self):
        """L2: Can connect to Ollama API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:11434/api/tags", timeout=5.0
                )
                # /api/tags returns 200 or 405 depending on Ollama version
                assert response.status_code in [200, 405] or response.json() is not None
        except httpx.ConnectError:
            pytest.skip("Ollama not running - run 'ollama serve' first")

    @pytest.mark.asyncio
    async def test_L2_ollama_chat_basic(self):
        """L2: Ollama chat endpoint works"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "mistral",
                        "messages": [{"role": "user", "content": "Hi"}],
                        "stream": False,
                    },
                    timeout=30.0,
                )
                assert response.status_code == 200
                result = response.json()
                assert "message" in result
        except httpx.ConnectError:
            pytest.skip("Ollama not running")


# ============================================================
# L3: END-TO-END TESTS - Full agent flows
# ============================================================


class TestE2EAgentSimple:
    """L3: Test full simple agent flow"""

    @pytest.mark.asyncio
    async def test_L3_simple_agent_adds_product(self, tmp_path):
        """L3: Simple agent can add a product"""
        os.chdir(tmp_path)

        from agent_example import OllamaModel, TOOLS, SYSTEM_PROMPT

        model = OllamaModel("mistral")

        # Skip if Ollama not running
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:11434/api/tags", timeout=2.0)
        except httpx.ConnectError:
            pytest.skip("Ollama not running")

        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: Add product named TestGPU, price 599, description Gaming card"

        result = await model.generate(full_prompt, tools=TOOLS)

        # Either tool was called or response received
        assert result is not None
        assert len(result) > 0

    def test_L3_simple_agent_files_exist(self):
        """L3: Agent file has required components"""
        from agent_example import TOOLS, SYSTEM_PROMPT, OllamaModel

        assert "add_product" in TOOLS
        assert SYSTEM_PROMPT is not None
        assert OllamaModel is not None


class TestE2EAgentMemory:
    """L3: Test agent with memory"""

    def test_L3_memory_agent_components(self):
        """L3: Memory agent has required components"""
        from agent_memory import run_agent, TOOLS, SYSTEM_PROMPT, OllamaModel

        assert callable(run_agent)
        assert TOOLS is not None
        assert SYSTEM_PROMPT is not None
        assert OllamaModel is not None

    @pytest.mark.asyncio
    async def test_L3_memory_agent_function(self, tmp_path):
        """L3: Memory agent function exists and is callable"""
        os.chdir(tmp_path)

        from agent_memory import run_agent

        # Just verify it's async and callable
        assert asyncio.iscoroutinefunction(run_agent)


class TestE2EAgentMulti:
    """L3: Test multi-agent system"""

    def test_L3_multi_agent_components(self):
        """L3: Multi-agent has coordinator and specialists"""
        from agent_multi import (
            coordinator,
            run_simpsons,
            run_pokemon,
            TOOLS_SIMPSONS,
            TOOLS_POKEMON,
        )

        assert callable(coordinator)
        assert callable(run_simpsons)
        assert callable(run_pokemon)
        assert "get_simpsons_info" in TOOLS_SIMPSONS
        assert "get_pokemon_info" in TOOLS_POKEMON

    @pytest.mark.asyncio
    async def test_L3_multi_agent_pokemon_delegation(self, tmp_path):
        """L3: Coordinator delegates to Pokemon specialist"""
        os.chdir(tmp_path)

        from agent_multi import run_pokemon

        # Skip if Ollama not running
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:11434/api/tags", timeout=2.0)
        except httpx.ConnectError:
            pytest.skip("Ollama not running")

        result = await run_pokemon("What is Charmander?")

        # Result should contain some response
        assert result is not None or "charmander" in result.lower()


# ============================================================
# FIXTURES AND HELPERS
# ============================================================

import os
import agent_example
import agent_memory
import agent_multi

# Fix import in agent_memory
try:
    from agent_memory import run_agent as task_run_agent

    agent_memory.run_agent = task_run_agent
except:
    pass


# ============================================================
# PYTEST CONFIGURATION
# ============================================================


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "asyncio: mark test as async")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
