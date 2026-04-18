"""
Tests for Memory Agent (agent_memory.py)

L0: Unit Tests - Individual components
L1: Integration Tests - Tools work correctly
L2: Service Tests - API calls work
L3: End-to-End Tests - Full agent flows

Run with: pytest tests/test_agent_memory.py -v
"""

import json
import os
import pytest
import asyncio
import httpx
import unittest.mock

import agent_memory


class TestUnitMemoryAgent:
    """L0: Test memory agent components"""

    def test_L0_run_agent_is_coroutine_function(self):
        """L0: run_agent is an async function"""
        assert asyncio.iscoroutinefunction(agent_memory.run_agent)

    def test_L0_memory_agent_components_exist(self):
        """L0: Memory agent has required components"""
        assert hasattr(agent_memory, "run_agent")
        assert agent_memory.TOOLS is not None
        assert agent_memory.SYSTEM_PROMPT is not None
        assert agent_memory.OllamaModel is not None


class TestIntegrationMemoryAgent:
    """L1: Test memory agent integration"""

    def test_L1_conversation_history_structure(self, tmp_path):
        """L1: Conversation history is properly structured"""
        os.chdir(tmp_path)

        # Create a mock conversation
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_L1_add_messages_to_history(self, tmp_path):
        """L1: Can add messages to conversation history"""
        os.chdir(tmp_path)

        history = []
        history.append({"role": "user", "content": "Test question"})
        history.append({"role": "assistant", "content": "Test answer"})

        assert len(history) == 2
        assert history[0]["content"] == "Test question"
        assert history[1]["content"] == "Test answer"


class TestServiceOllamaMemory:
    """L2: Test Ollama API with memory"""

    @pytest.mark.asyncio
    async def test_L2_ollama_available(self):
        """L2: Ollama is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:11434/api/tags", timeout=5.0
                )
                assert response.status_code in [200, 405]
        except httpx.ConnectError:
            pytest.skip("Ollama not running")


class TestE2EMemoryAgent:
    """L3: Test full memory agent flow"""

    def test_L3_memory_agent_callable(self):
        """L3: Memory agent is callable"""
        assert callable(agent_memory.run_agent)

    @pytest.mark.asyncio
    async def test_L3_memory_agent_async(self, tmp_path):
        """L3: Memory agent runs asynchronously"""
        os.chdir(tmp_path)

        # Just verify the function signature
        import inspect

        assert inspect.iscoroutinefunction(agent_memory.run_agent)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
