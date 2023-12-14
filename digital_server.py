import asyncio
import logging
import os
from asyncio import Queue
from typing import Dict, Optional, List

from pydantic import BaseModel

from TTS import TTService
from digitalman.livestreaming.livestream import DouyinMessageParser, UserBarrageMessage, WebcastMemberMessage, \
    WebcastLikeMessage
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import json

from SentimentEngine import SentimentEngine
from digitalman.digital_gpt import GPTService
import uuid

# 创建或获取一个 logger 对象
logger = logging.getLogger(__name__)

# 设置 logger 的日志级别
logger.setLevel(logging.INFO)

# 创建一个 handler 对象用于输出日志信息
handler = logging.StreamHandler()

# 创建一个 formatter 对象用于设置日志信息最后的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# 将 formatter 对象添加到 handler 对象
handler.setFormatter(formatter)

# 将 handler 对象添加到 logger 对象
logger.addHandler(handler)

app = FastAPI()

char_name = {
    'paimon': ['TTS/models/paimon6k.json', 'TTS/models/paimon6k_390k.pth', 'character_paimon', 1],
    'yunfei': ['TTS/models/yunfeimix2.json', 'TTS/models/yunfeimix2_53k.pth', 'character_yunfei', 1.1],
    'catmaid': ['TTS/models/catmix.json', 'TTS/models/catmix_107k.pth', 'character_catmaid', 1.2]
}

temp_filepath = "F:\\AI\\DigitalMan\\Files\\"


class SocketMessage(BaseModel):
    event: str
    state_index: int = None
    message: str = ''
    audio_path: str = None


class RoleManager:

    def __init__(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as file:
            self.data = json.load(file)

    def get_prompt_for_role(self, role):
        return self.data.get(role, {}).get("prompt", None)


class Chat:

    def __init__(self, websocket: WebSocket, client_id: str):
        self.ws = websocket
        self.client_id = client_id
        self.gpt_service = GPTService()
        # Sentiment Engine
        self.sentiment = SentimentEngine.SentimentEngine('SentimentEngine/models/paimon_sentiment.onnx')
        self.tts = TTService.TTService(*char_name['paimon'])
        self.wavfile = "{uuid}.wav"

    async def connect(self):
        await self.ws.accept()

    async def send_greet_message(self, message: str):
        voice_path = self.gen_voice(message)
        socket_message = SocketMessage(event='greet-event', message=message, state_index=1, audio_path=voice_path)
        send_msg = json.dumps(socket_message.dict(), ensure_ascii=False)
        await self.ws.send_text(send_msg)
        logger.info(f"Send greet message: {send_msg}")
        await self.send_end_message()

    async def handler_message(self, message: str):
        logger.info(f"receive message: {message}")

        try:
            data = json.loads(message)

            role = data['role']
            system_prompt = role_manager.get_prompt_for_role(role)
            self.gpt_service.update(role, system_prompt)

            prompt = data['prompt']
        except json.JSONDecodeError as e:
            logger.error(f"An error occurred while decoding JSON: {e}")
            prompt = message

        generator = self.gpt_service.chat_stream(prompt)
        for event, sentence in generator:
            senti = self.sentiment.infer(sentence)
            voice_path = self.gen_voice(sentence)
            socket_message = SocketMessage(event=event, message=sentence, state_index=senti, audio_path=voice_path)
            send_txt = json.dumps(socket_message.dict(), ensure_ascii=False)
            await self.ws.send_text(send_txt)
            logger.info(f"Send message: {send_txt}")
        await self.send_end_message()
        logger.info("Send end message")

    def gen_voice(self, resp_text, senti_or=None):
        tmp_proc_file = self.wavfile.format(uuid=uuid.uuid1())
        self.tts.read_save(resp_text, temp_filepath + tmp_proc_file, self.tts.hps.data.sampling_rate)

        return tmp_proc_file

    async def send_end_message(self):
        sm = SocketMessage(event='end')
        await self.ws.send_text(json.dumps(sm.dict(), ensure_ascii=False))


class ChatManager:
    def __init__(self):
        self.active_chats: Dict[str, Chat] = {}

    async def connect(self, client_id: str, chat: Chat):
        await chat.connect()
        self.active_chats[client_id] = chat

    def get_chat(self, client_id: str) -> Optional[Chat]:
        return self.active_chats[client_id]

    def disconnect(self, client_id: str):
        del self.active_chats[client_id]


role_manager = RoleManager("digitalman/roles.json")
manager = ChatManager()


class DigitalConsumer:
    chat_manager: ChatManager

    def __init__(self, chat_manager: ChatManager):
        self.chat_manager = chat_manager

    async def start_consumer(self, client_id: str, queue: Queue):
        last_message_time = asyncio.get_running_loop().time()
        chat = self.chat_manager.get_chat(client_id)

        while True:
            messages: List[UserBarrageMessage] = []
            start_time = asyncio.get_running_loop().time()
            if not queue.empty():
                ubm = await queue.get()
                print(f"Queue Message: {ubm}")
                msg_type = ubm.message.msg_type
                if msg_type == WebcastMemberMessage:
                    nickname = ubm.user.nickname
                    await chat.send_greet_message(f'欢迎{nickname}')
                    last_message_time = asyncio.get_running_loop().time()
                    continue
                elif msg_type == WebcastLikeMessage:
                    nickname = ubm.user.nickname
                    await chat.send_greet_message(f'感谢{nickname}的点赞')
                    last_message_time = asyncio.get_running_loop().time()
                    continue

            # 收集 10 秒内的所有消息
            while asyncio.get_running_loop().time() - start_time < 10 and len(messages) < 8:
                if ubm is not None:
                    messages.append(ubm)
                    last_message_time = asyncio.get_running_loop().time()
                await asyncio.sleep(0.1)  # 休眠 100 毫秒，减少 CPU 使用

            if messages:
                await self.process_messages(messages, chat)
            elif asyncio.get_running_loop().time() - last_message_time > 60:
                # 进行额外处理
                await chat.handler_message(self.build_role_prompt("【平台】空闲"))
                last_message_time = asyncio.get_running_loop().time()

    async def process_messages(self, messages, chat):
        # 处理消息
        l = len(messages)
        if l <= 3:
            format_messages = self.format_messages(messages)
            await chat.handler_message(self.build_role_prompt("\n".join(format_messages)))
        else:
            format_messages = self.format_messages(messages)
            if format_messages is None:
                print("process messages,but it is none, length={l}")
                return

            print(f"多消息格式化列表: {format_messages}")

            msg_list = "\n".join(f"- {item}" for item in format_messages)
            prompt = f"""
                            从消息列表中随机挑选3条进行回复,但是在回复中不要提示你选了那几条消息.

                            ## 消息列表
                            {msg_list}

                            ---

                            ## 消息挑选规则
                            - 增加礼物挑选中的权重
                            - 忽略无效的消息，比如： 111、222等
                            """
            role = 'paimon'

            await chat.handler_message(self.build_role_prompt(prompt))

    def build_role_prompt(self, prompt: str):
        return json.dumps({"role": 'paimon', "prompt": prompt})

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
            asyncio.create_task(self.digital_consumer.start_consumer(client_id=client_id,
                                                                     queue=queue))  # Start a new consumer if none exists
        await queue.put(user_barrage_msg)


digital_queue = DigitalQueue(chat_manager=manager)


@app.websocket("/ws/livestream/{client_id}")
async def websocket_livestream(websocket: WebSocket, client_id: str):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        print(message)
        user_barrage_message = DouyinMessageParser.parse_json(message)
        if user_barrage_message is not None:
            await digital_queue.producer(client_id, user_barrage_message)
            print("消息放到队列成功")


@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    chat = Chat(websocket, client_id)
    await manager.connect(client_id=client_id, chat=chat)
    try:
        while True:
            message = await websocket.receive_text()
            await chat.handler_message(message)
    except WebSocketDisconnect:
        logger.error("数字人socket断开连接")
        manager.disconnect(client_id)


@app.get("/download/{file_name}")
async def download_file(file_name: str):
    # 检查文件是否存在
    file_path = os.path.join(temp_filepath, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 返回文件响应
    return FileResponse(file_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=32222)
