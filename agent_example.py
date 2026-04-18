import json
import httpx
import asyncio

SYSTEM_PROMPT = """
You are an assistant that helps add products to a JSON database.
When user asks to add a product, you MUST call the add_product tool with the name, price, and description.
DO NOT explain the code - actually call the tool.
Return only the final result after calling the tool.
"""


def add_product(name: str, price: str, description: str) -> str:
    """Add a product to the JSON database"""
    try:
        try:
            with open("datos.json", "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        new_product = {"name": name, "price": price, "description": description}

        data.append(new_product)
        with open("datos.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        return f"Product '{name}' added successfully!"

    except Exception as e:
        return f"Error adding product: {e}"


TOOLS = {"add_product": add_product}


class OllamaModel:
    def __init__(self, model_name="mistral"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"

    async def generate(self, prompt, tools=None):
        url = f"{self.base_url}/api/chat"

        messages = [{"role": "user", "content": prompt}]

        payload = {"model": self.model_name, "messages": messages, "stream": False}

        if tools:
            tool_defs = []
            for name, func in tools.items():
                tool_defs.append(
                    {
                        "type": "function",
                        "function": {
                            "name": name,
                            "description": func.__doc__ or "",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "price": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                                "required": ["name", "price", "description"],
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

            # Parse content as JSON if tool_calls is empty but content looks like tool call
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

                    if func_name in TOOLS:
                        tool_result = TOOLS[func_name](
                            name=args.get("name", ""),
                            price=args.get("price", ""),
                            description=args.get("description", ""),
                        )

                        messages.append(
                            {
                                "role": "assistant",
                                "content": content,
                            }
                        )
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


async def run_agent(user_input):
    model = OllamaModel("mistral")
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_input}"
    result = await model.generate(full_prompt, tools=TOOLS)
    return result


def test():
    print("Product Agent with Ollama Mistral")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        result = asyncio.run(run_agent(user_input))
        print(f"Agent: {result}\n")


if __name__ == "__main__":
    test()
