from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from general_agent import GeneralChatGPT

from dotenv import load_dotenv

load_dotenv()

general_chat_gpt = GeneralChatGPT.from_llm_and_tools(memory=ConversationBufferMemory(return_messages=True),
                                          llm=ChatOpenAI(temperature=0.5),
                                          # system_base_prompt="我想要你扮演一位python高级工程师",
                                                     verbose=True)

while True:
    q = input("Enter:")
    res = general_chat_gpt.run(q)
    print(res)

