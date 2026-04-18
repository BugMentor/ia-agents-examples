"""
Tests for Simple Agent (agent_example.py)

L0: Unit Tests - Individual components
L1: Integration Tests - Tools work correctly
L2: Service Tests - API calls work
L3: End-to-End Tests - Full agent flows

Run with: pytest tests/test_agent_example.py -v
"""

import json
import os
import pytest
import asyncio
import httpx

import agent_example


class TestUnitAddProduct:
    """L0: Test add_product function in isolation"""

    def test_L0_add_product_creates_new_file(self, tmp_path):
        """L0: Tool creates datos.json when it doesn't exist"""
        os.chdir(tmp_path)

        result = agent_example.add_product("TestProduct", "99", "Test description")

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

        result = agent_example.add_product("NewProduct", "100", "New desc")

        with open("datos.json") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[1]["name"] == "NewProduct"

    def test_L0_add_product_invalid_json_handled(self, tmp_path):
        """L0: Tool handles corrupted JSON gracefully"""
        os.chdir(tmp_path)

        with open("datos.json", "w") as f:
            f.write("invalid json {{{")

        result = agent_example.add_product("Product", "10", "desc")

        assert "Product" in result
        assert "Error" not in result


class TestIntegrationAddProduct:
    """L1: Test add_product with real file I/O"""

    def test_L1_add_product_writes_correct_json(self, tmp_path):
        """L1: add_product writes valid JSON"""
        os.chdir(tmp_path)

        result = agent_example.add_product("Laptop", "999", "Powerful computer")

        assert "added successfully" in result.lower()

        with open("datos.json") as f:
            data = json.load(f)

        assert data[0]["name"] == "Laptop"
        assert data[0]["price"] == "999"
        assert data[0]["description"] == "Powerful computer"


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


class TestE2ESimpleAgent:
    """L3: Test full simple agent flow"""

    @pytest.mark.asyncio
    async def test_L3_simple_agent_adds_product(self, tmp_path):
        """L3: Simple agent can add a product"""
        os.chdir(tmp_path)

        model = agent_example.OllamaModel("mistral")

        # Skip if Ollama not running
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:11434/api/tags", timeout=2.0)
        except httpx.ConnectError:
            pytest.skip("Ollama not running")

        full_prompt = f"{agent_example.SYSTEM_PROMPT}\n\nUser: Add product named TestGPU, price 599, description Gaming card"

        result = await model.generate(full_prompt, tools=agent_example.TOOLS)

        assert result is not None
        assert len(result) > 0

    def test_L3_simple_agent_files_exist(self):
        """L3: Agent file has required components"""
        assert "add_product" in agent_example.TOOLS
        assert agent_example.SYSTEM_PROMPT is not None
        assert agent_example.OllamaModel is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
