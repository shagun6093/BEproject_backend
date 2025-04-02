from model import assistant
from langchain_core.messages import HumanMessage
from utils import State

user = [HumanMessage(content="Hi, my name is John and I had a very bad day. I feel like I am useless and will never become anything in life. I am not sure if I can do this anymore. I am so anxious and nervous about everything. I just want to be happy and confident again. Can you help me?"),]
config = {"configurable": {"thread_id": 123}}

# initial_state = State(messages=user, user_input=user.content, distortion=[], task="")

response = assistant.invoke({"messages": user, "user_input": user[-1].content, "distortion": [], "task": ""}, config)

print(response["messages"])

user1 = [HumanMessage(content="Can you tell me my name?")]

response1 = assistant.invoke({"messages": user1, "user_input": user1[-1].content, "distortion": response["distortion"], "task": response["task"]}, config)

print(response1["messages"])