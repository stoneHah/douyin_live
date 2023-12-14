from typing import List, Callable, Any

from langchain import LLMChain
from langchain.chat_models.base import BaseChatModel
from langchain.memory.chat_memory import BaseChatMemory
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import BaseMessage, SystemMessage, HumanMessage
from langchain.tools import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever
from pydantic import BaseModel


class GeneralChatGPTPrompt(BaseChatPromptTemplate, BaseModel):
    tools: List[BaseTool]
    token_counter: Callable[[str], int]
    send_token_limit: int = 4097

    def construct_full_prompt(self, system_base_prompt: str) -> str:
        if system_base_prompt is None:
            system_base_prompt = """Assistant is a large language model trained by OpenAI.

            Assistant is designed to be able to assist with a wide range of tasks, 
            from answering simple questions to providing in-depth explanations and 
            discussions on a wide range of topics. As a language model, Assistant is 
            able to generate human-like text based on the input it receives, 
            allowing it to engage in natural-sounding conversations and 
            provide responses that are coherent and relevant to the topic at hand."""

        # Construct full prompt
        full_prompt = system_base_prompt

        # if(len(self.tools) > 0):
        #     full_prompt += f"\n\n{get_prompt(self.tools)}"

        return full_prompt

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        base_prompt = SystemMessage(content=self.construct_full_prompt(kwargs["system_base_prompt"]))
        messages: List[BaseMessage] = [base_prompt]

        used_tokens = self.token_counter(base_prompt.content)
        retriever: VectorStoreRetriever = kwargs["retriever"]
        memory: BaseChatMemory = kwargs["memory"]
        user_input = kwargs["user_input"]

        if retriever:
            relevant_docs = retriever.get_relevant_documents(user_input)
            relevant_page_content = [d.page_content for d in relevant_docs]
            relevant_memory_tokens = sum(
                [self.token_counter(doc) for doc in relevant_page_content]
            )
            while used_tokens + relevant_memory_tokens > 2500:
                relevant_page_content = relevant_page_content[:-1]
                relevant_memory_tokens = sum(
                    [self.token_counter(doc) for doc in relevant_page_content]
                )
            content_format = (
                f"Use the following pieces of context to answer the question at the end. "
                f"If you don't know the answer, just say that you don't know, "
                f"don't try to make up an answer.\n\n{relevant_page_content}"
            )
            context_message = SystemMessage(content=content_format)
            used_tokens += len(context_message.content)

            messages.append(context_message)

        previous_messages = memory.load_memory_variables({}).get(memory.memory_key)
        historical_messages: List[BaseMessage] = []
        if previous_messages:
            for message in previous_messages[-10:][::-1]:
                message_tokens = self.token_counter(message.content)
                if used_tokens + message_tokens > self.send_token_limit - 1000:
                    break
                used_tokens += message_tokens
                historical_messages = [message] + historical_messages
        input_message = HumanMessage(content=kwargs["user_input"])

        messages += historical_messages
        messages.append(input_message)
        return messages


class GeneralChatGPT:

    def __init__(
            self,
            memory: BaseChatMemory,
            retriever: VectorStoreRetriever,
            chain: LLMChain,
            system_base_prompt: str,
            tools: List[BaseTool] = [],
    ):
        self.memory = memory
        self.retriever = retriever
        self.chain = chain
        self.tools = tools
        self.system_base_prompt = system_base_prompt

    @classmethod
    def from_llm_and_tools(
            cls,
            memory: BaseChatMemory,
            llm: BaseChatModel,
            retriever: VectorStoreRetriever = None,
            tools: List[BaseTool] = [],
            system_base_prompt: str = None,
            verbose: bool = False
    ):
        memory.input_key = "user_input"

        prompt = GeneralChatGPTPrompt(
            tools=tools,
            input_variables=["retriever", "memory", "user_input", "system_base_prompt"],
            token_counter=llm.get_num_tokens,
        )
        chain = LLMChain(llm=llm, prompt=prompt,memory=memory,verbose=verbose)
        return cls(
            memory,
            retriever,
            chain,
            system_base_prompt,
            tools
        )

    def run(self, input: str) -> str:
        return self.chain.run(
                system_base_prompt=self.system_base_prompt,
                retriever=self.retriever,
                memory=self.memory,
                user_input=input,
            )

    async def arun(self, input: str):
        self.chain.run(
            system_base_prompt=self.system_base_prompt,
            retriever=self.retriever,
            memory=self.memory,
            user_input=input,
        )