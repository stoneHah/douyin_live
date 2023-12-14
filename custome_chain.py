from typing import List, Callable, Any

from dotenv import load_dotenv
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.llms import BaseLLM
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_message_histories import RedisChatMessageHistory
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate, BaseChatPromptTemplate
from langchain.schema import BaseChatMessageHistory, BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever
from pydantic import BaseModel

load_dotenv()


class CustomeConversationChain(LLMChain):

    @classmethod
    def from_llm(cls, llm: ChatOpenAI, chat_memory: BaseChatMessageHistory, system_prompt: str = None,
                 verbose: bool = False):
        #  memory
        memory = ConversationBufferWindowMemory(memory_key="chat_history", chat_memory=chat_memory,
                                                k=5)

        pre_messages = [];
        if system_prompt:
            pre_messages.append(SystemMessagePromptTemplate.from_template(system_prompt))

        system_template = "The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.\n\nCurrent conversation:\n{chat_history}\nHuman: {human_input}\nAI:"
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        pre_messages.append(system_message_prompt)

        chat_prompt = ChatPromptTemplate.from_messages(pre_messages)

        return cls(prompt=chat_prompt, llm=llm, memory=memory, verbose=verbose)


