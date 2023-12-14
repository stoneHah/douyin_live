import asyncio
import logging
import threading
import time
from typing import Any, Dict, List, Union, Tuple

from dotenv import load_dotenv
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import LLMResult

from general_agent import GeneralChatGPT

load_dotenv()

STOP_TOKEN = '#!stop!#'
EVENT_NEW_TOKEN = 'new_token'
EVENT_ACTION_START = 'action_start'
EVENT_ACTION_END = 'action_end'
EVENT_END = 'end'

logger = logging.getLogger(__name__)


class StreamTokenBuffer:
    buffer: List[Tuple[str, str]] = []

    def __init__(self):
        self.buffer = []

    def add_to_buffer(self, event: str, token: str):
        self.buffer.append((event, token))

    def stream_tokens(self):
        while True:
            # when we didn't receive any token yet, just continue
            if len(self.buffer) == 0:
                time.sleep(0.1)
                continue

            event, token = self.buffer.pop(0)

            yield event, token

            if event == EVENT_END:
                break


class StreamingLLMCallbackHandler(BaseCallbackHandler, StreamTokenBuffer):
    """Callback handler for streaming LLM responses."""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.add_to_buffer(EVENT_NEW_TOKEN, token)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        self.add_to_buffer(EVENT_END, '')

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        pass

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        pass


from datetime import datetime


class GPTService:
    def __init__(self, model_name="gpt-3.5-turbo", system_prompt: str = None, verbose=True):
        self.model_name = model_name
        self.temperature = 0.7
        self.internet = False
        self.verbose = verbose
        self.system_prompt = system_prompt
        self.role = None

        #  memory
        self.memory = ConversationBufferWindowMemory(memory_key="chat_history",
                                                     k=5, return_messages=True)

    def chat_stream(self, prompt: str):
        # llm
        stream_handler = StreamingLLMCallbackHandler()
        llm = ChatOpenAI(streaming=True, model_name=self.model_name,
                         callback_manager=CallbackManager([stream_handler]), verbose=self.verbose,
                         temperature=self.temperature)
        agent_chain = GeneralChatGPT.from_llm_and_tools(memory=self.memory,
                                                        llm=llm,
                                                        system_base_prompt=self.system_prompt,
                                                        verbose=self.verbose
                                                        )

        def query():
            res = agent_chain.run(input=prompt)
            print(res)

        t = threading.Thread(target=query)
        t.start()

        def event_generator(stream_token_buffer: StreamTokenBuffer):
            sentence = ""
            punctuation_marks = {"!", "。", "?", ";", "!", ".", "！", "？"}  # 可以添加更多标识句子结束的标点符号

            for event, token in stream_token_buffer.stream_tokens():
                # logger.info(f"event={event},token={token}")
                if not token.strip():  # 如果是空白字符则忽略
                    continue

                sentence += token  # 将token添加到当前句子

                # logger.info(f"sentence={sentence}")
                # 检查句子是否已经完成（以标点符号结尾）
                if token in punctuation_marks and len(sentence) > 20:
                    yield event, sentence
                    sentence = ""  # 清空当前句子，准备接收下一个句子

            # 如果已经到了最后，但是sentence不为空，则返回sentence
            if len(sentence) > 0:
                yield EVENT_NEW_TOKEN, sentence

        return event_generator(stream_handler)

    def update(self, new_role, new_system_prompt):
        old_role = self.role
        self.role = new_role
        self.system_prompt = new_system_prompt

        if old_role is not None and old_role != new_role:
            # 清空memory
            self.memory.clear()
            pass


if __name__ == "__main__":
    gpt = GPTService(system_prompt='# role'
                                   '你是一个擅长聊天的超级无敌美少女'
                                   '# constraint'
                                   '每次回复的内容尽量简洁，不要超过50个字')
    while True:
        prompt = input("question:")
        generator = gpt.chat_stream(prompt)
        for item in generator:
            print(f"Received item: {item}")
