from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    HumanMessage,
)

from langchain.callbacks.base import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from dotenv import load_dotenv

load_dotenv()

chat = ChatOpenAI(streaming=True,model_name = 'gpt-3.5-turbo', callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]), verbose=True, temperature=0.6)
resp = chat([HumanMessage(content="hello")])
print(resp)
