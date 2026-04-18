import json
import httpx
import asyncio
import requests
from pydantic import BaseModel

SYSTEM_PROMPT_COORDINATOR = """
You are a coordinator of a team of agents.
You must delegate to the appropriate specialist agent based on the query.

Available specialists:
- simpsons_agent: Expert in The Simpsons TV series. Use for questions about Homer, Bart, Lisa, Marge, etc.
- pokemon_agent: Expert in Pokemon. Use for questions about Pikachu, Charizard, etc.

If the user asks about The Simpsons characters, delegate to simpsons_agent.
If the user asks about Pokemon, delegate to pokemon_agent.
Always respond in the same language as the query.
Respond directly without explaining the delegation process.
"""

SYSTEM_PROMPT_SIMPSONS = """
You are an expert in The Simpsons TV series.
You have a tool 'get_simpsons_info' to look up character information from the Simpsons API.
Use it when the user asks about Simpsons characters.
Provide detailed information about the character.
"""

SYSTEM_PROMPT_POKEMON = """
You are an expert in Pokemon.
You have a tool 'get_pokemon_info' to look up Pokemon information from PokeAPI.
Use it when the user asks about Pokemon.
Provide information about type, abilities, and other stats.
"""


def get_simpsons_info(character_name: str) -> str:
    """Get information about a Simpsons character"""
    try:
        response = requests.get("https://thesimpsonsapi.com/api/characters", timeout=10)
        if response.status_code == 200:
            characters = response.json()
            for char in characters:
                if char["name"].lower() == character_name.lower():
                    return f"{char['name']}: {char['description']}"
            return "Character not found."
        return "Error fetching Simpsons data."
    except Exception as e:
        return f"Error: {e}"


def get_pokemon_info(pokemon_name: str) -> str:
    """Get information about a Pokemon"""
    try:
        response = requests.get(
            f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}", timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            types = [t["type"]["name"] for t in data["types"]]
            abilities = [a["ability"]["name"] for a in data["abilities"]]
            return f"{data['name'].title()}: Types: {', '.join(types)}. Abilities: {', '.join(abilities)}."
        return "Pokemon not found."
    except Exception as e:
        return f"Error: {e}"


TOOLS_SIMPSONS = {"get_simpsons_info": get_simpsons_info}
TOOLS_POKEMON = {"get_pokemon_info": get_pokemon_info}


class OllamaModel:
    def __init__(self, model_name="mistral"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"

    async def generate(self, messages, tools=None):
        url = f"{self.base_url}/api/chat"
        payload = {"model": self.model_name, "messages": messages, "stream": False}

        if tools:
            tool_defs = []
            for name, func in tools.items():
                params = (
                    {"character_name": {"type": "string"}}
                    if "simpsons" in name
                    else {"pokemon_name": {"type": "string"}}
                )
                required = (
                    ["character_name"] if "simpsons" in name else ["pokemon_name"]
                )

                tool_defs.append(
                    {
                        "type": "function",
                        "function": {
                            "name": name,
                            "description": func.__doc__ or "",
                            "parameters": {
                                "type": "object",
                                "properties": params,
                                "required": required,
                            },
                        },
                    }
                )
            payload["tools"] = tool_defs

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            result = response.json()

            message = result.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])

            if not tool_calls and content.strip().startswith("["):
                try:
                    parsed = json.loads(content)
                    if parsed and isinstance(parsed[0], dict) and "name" in parsed[0]:
                        tool_calls = [{"function": parsed[0]}]
                except:
                    pass

            if tool_calls:
                for tc in tool_calls:
                    func_data = tc.get("function", {})
                    func_name = func_data.get("name")
                    args = func_data.get("arguments", {})

                    tools_map = {**TOOLS_SIMPSONS, **TOOLS_POKEMON}
                    if func_name in tools_map:
                        if "simpsons" in func_name:
                            tool_result = tools_map[func_name](
                                character_name=args.get("character_name", "")
                            )
                        else:
                            tool_result = tools_map[func_name](
                                pokemon_name=args.get("pokemon_name", "")
                            )

                        messages.append({"role": "assistant", "content": content})
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.get("id", "call_1"),
                                "content": tool_result,
                            }
                        )

                        payload["messages"] = messages
                        response2 = await client.post(url, json=payload, timeout=60.0)
                        result2 = response2.json()
                        final_msg = result2.get("message", {})
                        return final_msg.get("content", tool_result)

        return content


async def run_simpsons(user_input):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_SIMPSONS},
        {"role": "user", "content": user_input},
    ]
    model = OllamaModel("mistral")
    return await model.generate(messages, tools=TOOLS_SIMPSONS)


async def run_pokemon(user_input):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_POKEMON},
        {"role": "user", "content": user_input},
    ]
    model = OllamaModel("mistral")
    return await model.generate(messages, tools=TOOLS_POKEMON)


def coordinator(user_input):
    """Multi-agent coordinator - delegates to specialist"""
    user_lower = user_input.lower()

    if any(
        word in user_lower
        for word in ["simpsons", "homero", "bart", "lisa", "marge", "moe", "flanders"]
    ):
        print("-> Delegating to Simpsons specialist...")
        return asyncio.run(run_simpsons(user_input))

    elif any(
        word in user_lower
        for word in ["pokemon", "pikachu", "charizard", "bulbasaur", "squirtle"]
    ):
        print("-> Delegating to Pokemon specialist...")
        return asyncio.run(run_pokemon(user_input))

    else:
        return "I can help with Simpsons or Pokemon. Try asking about Homer, Bart, Pikachu, or Charizard!"


def test():
    print("Multi-Agent System (Coordinator + Simpsons + Pokemon)")
    print("=" * 55)
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        result = coordinator(user_input)
        print(f"Agent: {result}\n")


if __name__ == "__main__":
    test()
