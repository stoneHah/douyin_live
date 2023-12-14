from asyncio import Queue
from typing import Dict, List

from digital_server import ChatManager
from livestreaming.livestream import UserBarrageMessage

import asyncio


class DigitalConsumer:
    chat_manager: ChatManager

    def __init__(self, chat_manager: ChatManager):
        self.chat_manager = chat_manager

    async def start_consumer(self, client_id: str, queue: Queue):
        while True:
            messages: List[str] = []
            start_time = asyncio.get_running_loop().time()

            # 收集 10 秒内的所有消息
            while asyncio.get_running_loop().time() - start_time < 10:
                if not queue.empty():
                    messages.append(await queue.get())
                await asyncio.sleep(0.1)  # 休眠 100 毫秒，减少 CPU 使用

            chat = self.chat_manager.get_chat(client_id)
            await self.process_messages(messages, chat)

    async def process_messages(self, messages, chat):
        if messages:
            # 处理消息
            l = len(messages)
            if l <= 3:
                format_messages = self.format_messages(messages)
                await chat.handler_message(format_messages.join("\n"))
            else:
                format_messages = self.format_messages(messages)
                msg_list = format_messages.join("\n")
                await chat.handler_message(f"""
                从消息列表中随机挑选3条进行回复

                ## 消息列表
                {msg_list}
                
                ---
                
                ## 消息挑选规则
                - 增加礼物挑选中的权重
                - 忽略无效的消息，比如： 111、222等
                """)
        else:
            await chat.handler_message("【平台】空闲")

    def format_messages(self, messages) -> List[str]:
        format_messages = []
        for message in messages:
            if isinstance(message, UserBarrageMessage):
                format_messages.append(message.format())

        return format_messages


class DigitalQueue:
    queue_list: Dict[str, Queue] = {}

    chat_manager: ChatManager
    digital_consumer: DigitalConsumer

    def __init__(self, chat_manager: ChatManager):
        self.digital_consumer = DigitalConsumer(chat_manager)

    async def producer(self, client_id: str, user_barrage_msg: UserBarrageMessage):
        queue = self.queue_list.get(client_id)
        if queue is None:
            queue = asyncio.Queue()
            self.queue_list[client_id] = queue
            asyncio.create_task(self.digital_consumer.start_consumer(queue))  # Start a new consumer if none exists
        await queue.put(user_barrage_msg)


async def main():
    digital_queue = DigitalQueue()
    await digital_queue.producer('123', 'barr')
    await digital_queue.producer('123', 'barr123')
    await digital_queue.producer('123', 'barr234')
    await asyncio.sleep(5)


if __name__ == '__main__':
    # asyncio.run(main())
    msg_list = """【礼物】石头: 送了棒棒糖 
                【聊天】你喜欢哪些好吃的
                【聊天】你生活在生么样的大陆
                【聊天】你是谁
                【礼物】石头: 送了棒棒糖 
                【聊天】原神中有哪些有趣的故事
                """
    print(f"""
        从消息列表中随机挑选3条进行回复

        ## 消息列表
        {msg_list}

        ---

        ## 消息挑选规则
        - 增加礼物挑选中的权重
        - 忽略无效的消息，比如： 111、222等
        """)
