import uuid

from langchain.callbacks.manager import CallbackManager
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    PromptTemplate,
)
from pydantic import BaseModel


class Conversation(BaseModel):
    id: str = uuid.uuid4().hex
    name: str = "Conversation"
    llm_model_name: str = "gpt-3.5-turbo"
    system_role_desc: str = """Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

    Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.
    
    Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

    """


class ConversationFactory():
    """会话工厂"""

    def __init__(self):
        self.conversations = {}

    def create_conversation(self):
        conversation = Conversation(id=uuid.uuid4().hex)
        self.conversations[conversation.id] = conversation
        return conversation

    def get_conversation(self, conversation_id):
        return self.conversations[conversation_id]


variable_template = """
    {history}
    Human: {human_input}
    Assistant:"""


def gen_chain(c: Conversation, stream_handler, verbose=False):
    prompt = PromptTemplate(
        input_variables=["history", "human_input"],
        template=c.system_role_desc + variable_template
    )

    stream_manager = CallbackManager([stream_handler])

    # return LLMChain(
    #     llm=ChatOpenAI(temperature=0.6, model_name=c.llm_model_name, streaming=True,callback_manager=stream_manager),
    #     prompt=prompt,
    #     memory=ConversationBufferWindowMemory(k=2),
    #     verbose=verbose
    # )

    return ChatOpenAI(temperature=0.6, model_name=c.llm_model_name, streaming=True, callback_manager=stream_manager)
