import asyncio
import json
import logging
import re
from enum import Enum
from typing import List

import uvicorn
from pydantic import BaseModel

import digitalman.livestreaming.douyin_messages as douyin
from fastapi import FastAPI, WebSocket
import io
import sys
import tts

app = FastAPI()

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def setup_logger():
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.DEBUG)

    # 创建文件处理器
    file_handler = logging.FileHandler('douyin.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 创建控制台处理器
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)


setup_logger()

logger = logging.getLogger('my_logger')

message_queue = asyncio.Queue()

connections: List[WebSocket] = []

class GiftManager:

    def __init__(self):
        with open("digitalman/gifts.json", 'r', encoding='utf-8') as file:
            self.data = json.load(file)

    def get_video_url(self, gift_id):
        return self.data.get(gift_id,"http://localhost/xjj/xjj_2.mp4")

class CommandType(Enum):
    PLAY_VIDEO = "play_video"
    PLAY_AUDIO = "play_audio"
    # 添加更多命令...

class Command(BaseModel):
    command: CommandType
    data: str

class MessageProcessor:
    async def process(self, message, websocket):
        raise NotImplementedError


class ChatMessageProcessor(MessageProcessor):
    async def process(self, message, websocket):
        print(f'正在Chat处理消息: {message}')


def sanitize_nickname(nickname):
    # Remove or replace special characters
    return re.sub(r'[^\w\s]', '', nickname)


async def broadcast_command(command_message, sender_websocket):
    print(f'广播命令: {command_message}')
    for connection in connections:
        if connection != sender_websocket:
            await connection.send_text(command_message.json())

gift_manager = GiftManager()
class GiftMessageProcessor(MessageProcessor):
    async def process(self, message, websocket):
        print(f'正在处理消息: {message}')
        # 处理礼物消息的逻辑
        gift_id = message.gift_id
        gift_name = message.gift_name
        nick_name = sanitize_nickname(message.user_info.nick_name)
        thanks_info = f"感谢 {nick_name} 送的 {gift_name}"
        voice_filename = tts.gen_voice(thanks_info)

        # Broadcast a command message to other clients
        command_message = Command(command=CommandType.PLAY_AUDIO, data=f"http://localhost/audio_f/{voice_filename}")
        await broadcast_command(command_message, websocket)

        video_url = gift_manager.get_video_url(gift_id)
        await broadcast_command(Command(command=CommandType.PLAY_VIDEO, data=video_url), websocket)


class LikeMessageProcessor:
    async def process(self, message, websocket):
        print(f'正在处理消息: {message}')

class FollowMessageProcessor:
    async def process(self, message, websocket):
        print(f'正在处理消息: {message}')
        # 处理关注消息的逻辑
        nick_name = sanitize_nickname(message.user_info.nick_name)
        thanks_info = f"感谢 {nick_name} 的关注"
        voice_filename = tts.gen_voice(thanks_info)

        # Broadcast a command message to other clients
        command_message = Command(command=CommandType.PLAY_AUDIO, data=f"http://localhost/audio_f/{voice_filename}")
        await broadcast_command(command_message, websocket)

message_processors = {
    douyin.ChatMessage: ChatMessageProcessor(),
    douyin.GiftMessage: GiftMessageProcessor(),
    douyin.LikeMessage: LikeMessageProcessor(),
    douyin.FollowMessage: FollowMessageProcessor(),

}


async def process_messages(websocket: WebSocket):
    while True:
        msg = await message_queue.get()
        try:
            # 处理消息
            # ...
            processor = message_processors[type(msg)]
            if processor is None:
                logger.debug(f'No processor for message: {msg}')
                continue
            await processor.process(msg, websocket)
        except Exception as e:
            # 处理或记录异常
            logger.error(f'Error processing message: {e}')
        finally:
            # 确保调用 task_done，无论成功还是异常
            message_queue.task_done()


@app.websocket("/ws/livestream/{client_id}")
async def websocket_livestream(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connections.append(websocket)
    # 启动消息处理协程
    asyncio.create_task(process_messages(websocket))
    try:
        while True:
            message = await websocket.receive_text()
            try:
                douyin_msg = douyin.message_factory(message)
                print(f'收到消息: {douyin_msg}')
                await message_queue.put(douyin_msg)  # 将消息放入队列

            except ValueError:
                logger.debug(f'Unsupported message: {message}')
    except Exception as e:
        logger.error('client exception:{e}')
    finally:
        # 当 WebSocket 断开连接时执行
        connections.remove(websocket)


@app.websocket("/ws/consumer/{client_id}")
async def websocket_livestream(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connections.append(websocket)
    logger.info('a client connected to server')

    # await broadcast_command(Command(command=CommandType.PLAY_VIDEO, data="http://localhost/xjj/xjj_2.mp4"), websocket)

    try:
        while True:
            message = await websocket.receive_text()
            print(message)
    except Exception as e:
        logger.error('client exception:{e}')
    finally:
        connections.remove(websocket)


async def monitor_connections():
    while True:
        # 每隔一段时间检查一次
        await asyncio.sleep(10)  # 例如，每10秒检查一次
        # 打印或处理 connections 的信息
        print(f"当前连接数: {len(connections)}")

# 在应用启动时启动监控任务
@app.on_event("startup")
async def start_monitor():
    asyncio.create_task(monitor_connections())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=32222)
