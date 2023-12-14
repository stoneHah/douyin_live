import json
import re


class User:
    def __init__(self, nick_name: str, followed: bool = False, user_level: int = None):
        self.nick_name = nick_name
        self.followed = followed
        self.user_level = user_level


class Message:
    def __init__(self, json_str):
        self.data = json.loads(json_str)
        self.user_info = self.parse_user_info()
        self.process()

    def get_type(self):
        return self.data.get("type")

    def process(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def parse_user_info(self):
        user = self.data.get('user')
        if user is None:
            return None

        nickname = user.get('nickname')
        nickname_new = re.sub(r"\*+", "某某", nickname)
        followed = user.get('is_follower')
        return User(nick_name=nickname_new, followed=followed)


class ChatMessage(Message):
    """聊天消息"""

    def process(self):
        self.text = self.data.get('content', '')

    def __str__(self):
        return f"ChatMessage: {self.user_info.nick_name} | {self.text}"


class GiftMessage(Message):
    """刷礼物消息"""

    def process(self):
        gift_data = self.data.get("gift", {})
        self.gift_name = gift_data.get("name")
        self.gift_id = gift_data.get("id")

        # print(f"Gift Message: {gift_name}")

    def __str__(self):
        return f"GiftMessage: {self.user_info.nick_name} 送出 {self.gift_name} giftId:{self.gift_id}"


class FollowMessage(Message):
    """关注消息"""

    def process(self):
        pass

    def __str__(self):
        return f"FollowMessage:  {self.user_info.nick_name} 关注了主播"


class LikeMessage(Message):
    """点赞消息"""

    def process(self):
        pass

    def __str__(self):
        return f"LikeMessage:  {self.user_info.nick_name} 给主播点赞了"

class MemberMessage(Message):
    """用户进入直播间的消息"""

    def process(self):
        pass

    def __str__(self):
        return f"MemberMessage: {self.user_info.nick_name} 进入了直播间"


def message_factory(json_str):
    message_type_mapping = {
        "WebcastChatMessage": ChatMessage,
        "WebcastGiftMessage": GiftMessage,
        "WebcastLikeMessage": LikeMessage,
        "WebcastSocialMessage": FollowMessage,
        "WebcastMemberMessage": MemberMessage
    }

    json_data = json.loads(json_str)
    common_data = json_data.get('common', {})
    if common_data:
        msg_type = common_data.get('method')
        msg_class = message_type_mapping.get(msg_type)

        if msg_class:
            return msg_class(json_str)
        else:
            raise ValueError(f"Unsupported message")
    else:
        raise ValueError(f"Unsupported message")


