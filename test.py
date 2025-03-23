from model import assistant
from langchain_core.messages import HumanMessage
from utils import State

user = HumanMessage(content="I don't know, it was just fine.")
config = {"configurable": {"thread_id": 123}}

initial_state = State(messages=[user], user_input=user.content)

response = assistant.stream(initial_state, config)

print(response)