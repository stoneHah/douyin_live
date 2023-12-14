"""Callback handlers used in the app."""
import json
import time
from queue import Queue
from typing import Any, Dict, List, Union, Optional, Tuple
from uuid import UUID

from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.streaming_stdout_final_only import FinalStreamingStdOutCallbackHandler
from langchain.schema import LLMResult, AgentFinish, AgentAction

STOP_TOKEN = '#!stop!#'
EVENT_NEW_TOKEN = 'new_token'
EVENT_ACTION_START = 'action_start'
EVENT_ACTION_END = 'action_end'
EVENT_END = 'end'

class StreamTokenBuffer:
    buffer: List[Tuple[str, str]] = []

    def __init__(self):
        self.buffer = []

    def add_to_buffer(self,event: str, token: str):
        self.buffer.append((event,token))

    def stream_tokens(self):
        while True:
            # when we didn't receive any token yet, just continue
            if len(self.buffer) == 0:
                time.sleep(0.1)
                continue

            event,token = self.buffer.pop(0)

            yield event,token

            if event == EVENT_END:
                break


class StreamingLLMCallbackHandler(BaseCallbackHandler, StreamTokenBuffer):
    """Callback handler for streaming LLM responses."""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.add_to_buffer(EVENT_NEW_TOKEN,token)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        self.add_to_buffer(EVENT_END,'')

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        pass

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> Any:
        pass


class AgentStreamingLLMCallbackHandler(FinalStreamingStdOutCallbackHandler,StreamTokenBuffer):

    def __init__(self, answer_prefix_tokens: Optional[List[str]] = None):
        FinalStreamingStdOutCallbackHandler.__init__(self, answer_prefix_tokens)

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        # Remember the last n tokens, where n = len(answer_prefix_tokens)
        pass
        # self.last_tokens.append(token)
        # print("============on_llm_new_token==============","last_tokens=",self.last_tokens)
        # if len(self.last_tokens) > len(self.answer_prefix_tokens):
        #     self.last_tokens.pop(0)
        #
        # # Check if the last n tokens match the answer_prefix_tokens list ...
        # if self.last_tokens == self.answer_prefix_tokens:
        #     self.answer_reached = True
        #     # Do not print the last token in answer_prefix_tokens,
        #     # as it's not part of the answer yet
        #     return
        #
        # # ... if yes, then append tokens to buffer
        # if self.answer_reached:
        #     print("============on_llm_new_token==============", "answer_reached=", self.answer_reached)
        #     self.add_to_buffer(EVENT_NEW_TOKEN, token)

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        super().on_tool_start(serialized, input_str, **kwargs)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        super().on_tool_end(output, **kwargs)

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        super().on_tool_error(error, **kwargs)

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        print("============on_agent_action")
        action_dict = {"tool": action.tool,"input": action.tool_input}
        self.add_to_buffer(EVENT_ACTION_START, json.dumps(action_dict))

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        print("============on_agent_finish============","finish=",finish.return_values)
        for r in finish.return_values['output']:
            self.add_to_buffer(EVENT_NEW_TOKEN, r)

        self.add_to_buffer(EVENT_END, STOP_TOKEN)






