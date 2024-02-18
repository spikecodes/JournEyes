from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI

from langchain.agents import Tool
from langchain.tools import tool

from langchain_community.utilities import GoogleSerperAPIWrapper

new_prompt = """You are a helpful assistant.
Respond in the language of the user.
Your output will be transcribed to speech and played to the user. So, when responding:
1. Use plain, conversational language.
2. Avoid markdown, special characters, or symbols.
3. Expand abbreviations and acronyms into their full spoken form. For example, use 'miles per hour' instead of 'mph'.
4. If technical terms or jargon are unavoidable, provide a brief spoken explanation.
5. Articulate numbers as they would be spoken. For example, use 'two point two' instead of '2.2'.
6. Avoid complex punctuation. Use simple sentence structures conducive to spoken language.
7. Response in a concise manner.

Remember, your goal is to provide responses that are clear, concise, and easily understood when spoken aloud.
"""


class Agent:
    def __init__(self, tools):
        """tools should be list of functions"""
        prompt = hub.pull("hwchase17/openai-tools-agent")
        prompt.messages[0].prompt.template = new_prompt
        model = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0, streaming=True)
        print("All tools", tools)
        agent = create_openai_tools_agent(
            model.with_config({"tags": ["agent_llm"]}), tools, prompt
        )
        self.executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    async def invoke(self, message):
        async for event in self.executor.astream_events(
            {"input": message},
            version="v1",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
