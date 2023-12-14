from dotenv import load_dotenv
load_dotenv()


from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from datetime import datetime


class MyCustomHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"{current_time}My custom handler, token: {token}")





# To enable streaming, we pass in `streaming=True` to the ChatModel constructor
# Additionally, we pass in a list with our custom handler
chat = ChatOpenAI(max_tokens=25, streaming=True, callbacks=[MyCustomHandler()])

# 获取当前时间并格式化为字符串，精确到秒
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"Before chat: {current_time}")

conversation = ConversationChain(
    llm=chat,
    memory=ConversationBufferMemory()
)

conversation.run("Answer briefly. What are the first 3 colors of a rainbow?")