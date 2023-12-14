import logging
import re
from typing import Optional

from pydantic import BaseModel
import json
import asyncio

WebcastChatMessage = "WebcastChatMessage"
WebcastGiftMessage = "WebcastGiftMessage"
WebcastMemberMessage = "WebcastMemberMessage"
WebcastLikeMessage = "WebcastLikeMessage"


class Gift(BaseModel):
    name: str
    number: int


class Message(BaseModel):
    msg_type: str
    msg: str = None


class User(BaseModel):
    nickname: str
    followed: bool = False
    user_level: int = None


class UserBarrageMessage(BaseModel):
    # barrage_type: str
    user: User
    message: Message
    gift: Gift = None

    def format(self):
        msg_list = []
        msg_type = self.message.msg_type
        if msg_type == WebcastChatMessage:
            msg_list.append("【聊天】")
            msg_list.append(self.message.msg)
        elif msg_type == WebcastGiftMessage:
            msg_list.append("【礼物】")
            msg_list.append(self.message.msg)

        return "".join(msg_list)


def parse_user(json_data) -> Optional[User]:
    user = json_data.get('user')
    if user is None:
        return None

    nickname = user.get('nickname')
    nickname_new = re.sub(r"\*+", "某某", nickname)
    followed = user.get('is_follower')
    return User(nickname=nickname_new, followed=followed)


class DouyinMessageParser:

    @staticmethod
    def parse_json(json_str: str) -> Optional[UserBarrageMessage]:
        try:
            json_data = json.loads(json_str)
            common_data = json_data.get('common', {})
            if common_data:
                msg_type = common_data.get('method')
                if msg_type == 'WebcastChatMessage':
                    content = json_data.get('content', '')
                    message = Message(msg_type=msg_type, msg=content)
                    user = parse_user(json_data)
                    return UserBarrageMessage(user=user, message=message)

                elif msg_type == 'WebcastGiftMessage':
                    describe = common_data.get('describe')
                    message = Message(msg_type=msg_type, msg=describe)
                    user = parse_user(json_data)
                    return UserBarrageMessage(user=user, message=message)

                elif msg_type == WebcastMemberMessage:
                    message = Message(msg_type=msg_type)
                    user = parse_user(json_data)
                    return UserBarrageMessage(user=user, message=message)
                elif msg_type == WebcastLikeMessage:
                    message = Message(msg_type=msg_type)
                    user = parse_user(json_data)
                    return UserBarrageMessage(user=user, message=message)


            else:
                logging.error(f'还未识别的弹幕数据: {json_str}')

            # return User(name, age, email_address)
        except json.JSONDecodeError:
            return None


if __name__ == '__main__':
    # s = '{"chat_tags":[],"content":"求关注➕ 求关注➕ 求关注➕ 求关注➕ 求关注➕ 求关注➕ 求关注➕ 求关注➕ 求关注➕ 求关注➕","visible_to_sender":false,"full_screen_text_color":"","agree_msg_id":"0","priority_level":0,"event_time":"1697807324","send_review":false,"from_intercom":false,"intercom_hide_user_card":false,"chat_by":"0","individual_chat_priority":0,"common":{"method":"WebcastChatMessage","msg_id":"7292026903731442726","room_id":"7291917675155180297","create_time":"0","monitor":0,"is_show_msg":true,"describe":"","fold_type":"0","anchor_fold_type":"0","priority_score":"31062","log_id":"","msg_process_filter_k":"","msg_process_filter_v":"","anchor_fold_type_v2":"0","process_at_sei_time_ms":"0","random_dispatch_ms":"0","is_dispatch":false,"channel_id":"0","diff_sei2abs_second":"0","anchor_fold_duration":"0","app_id":"1128"},"user":{"badge_image_list":[],"real_time_icons":[],"new_real_time_icons":[],"top_fans":[],"media_badge_image_list":[],"commerce_webcast_config_ids":[],"badge_image_list_v2":[],"id":"3685175470864206","short_id":"22697311416","nickname":"招商总督导｜尚静虹","gender":2,"signature":"","level":0,"birthday":"0","telephone":"","verified":false,"experience":0,"city":"","status":0,"create_time":"0","modify_time":"0","secret":0,"share_qrcode_uri":"","income_share_percent":0,"special_id":"","top_vip_no":"0","pay_score":"0","ticket_count":"0","link_mic_stats":0,"display_id":"22697311416","with_commerce_permission":false,"with_fusion_shop_entry":false,"total_recharge_diamond_count":"0","verified_content":"","sec_uid":"MS4wLjABAAAAZSgD-cD2-orr8TsMmi3MwEUKI8_5g0B1ia5u8SzQAwypEEcCIDdVfMKwL3r-KpqH","user_role":0,"authorization_info":3,"adversary_authorization_info":0,"adversary_user_status":0,"location_city":"","remark_name":"","mystery_man":1,"web_rid":"","desensitized_nickname":"招商总督导｜尚静虹","is_anonymous":false,"consume_diamond_level":0,"webcast_uid":"MS4wLjPI2Mq1F47Lm0o_KJjH2hAYynvgx9NmxRfZjNAcbU_12f0mC0eRBxpLKsO2gjixFuo","allow_be_located":false,"allow_find_by_contacts":false,"allow_others_download_video":false,"allow_others_download_when_sharing_video":false,"allow_share_show_profile":false,"allow_show_in_gossip":false,"allow_show_my_action":false,"allow_strange_comment":false,"allow_unfollower_comment":false,"allow_use_linkmic":false,"bg_img_url":"","birthday_description":"","birthday_valid":false,"block_status":0,"comment_restrict":0,"constellation":"","disable_ichat":0,"enable_ichat_img":"0","exp":0,"fan_ticket_count":"0","fold_stranger_chat":false,"follow_status":"0","hotsoon_verified":false,"hotsoon_verified_reason":"","ichat_restrict_type":0,"id_str":"","is_follower":false,"is_following":false,"need_profile_guide":false,"pay_scores":"0","push_comment_status":false,"push_digg":false,"push_follow":false,"push_friend_action":false,"push_ichat":false,"push_status":false,"push_video_post":false,"push_video_recommend":false,"verified_mobile":false,"verified_reason":"","with_car_management_permission":false,"age_range":0,"watch_duration_month":"0","avatar_thumb":{"url_list":["https://p11.douyinpic.com/aweme/100x100/aweme-avatar/tos-cn-avt-0015_aec3028600c164dbac64d7cdab37fe95.jpeg?from=3067671334"],"flex_setting_list":[],"text_setting_list":[],"uri":"","height":"0","width":"0","avg_color":"","image_type":0,"open_web_url":"","is_animated":false},"follow_info":{"following_count":"53","follower_count":"141","follow_status":"1","push_status":"0","remark_name":"","follower_count_str":"0","following_count_str":"0","invalid_follow_status":false},"pay_grade":{"grade_icon_list":[],"total_diamond_count":"0","name":"","next_name":"","level":"0","next_diamond":"0","now_diamond":"0","this_grade_min_diamond":"0","this_grade_max_diamond":"0","pay_diamond_bak":"0","grade_describe":"","screen_chat_type":"0","upgrade_need_consume":"0","next_privileges":"","score":"0","grade_describe_shining":false,"grade_banner":""},"fans_club":{"prefer_data":{},"data":{"available_gift_ids":[],"club_name":"","level":0,"user_fans_club_status":0,"anchor_id":"0","badge_type":0,"badge":{"icons":{"0":{"url_list":[],"flex_setting_list":[],"text_setting_list":[],"uri":"","height":"0","width":"0","avg_color":"","image_type":0,"open_web_url":"","is_animated":false}},"title":""}}},"user_attr":{"admin_privileges":[],"is_muted":false,"is_admin":false,"is_super_admin":false}},"public_area_common":{"individual_strategy_result":{},"tracking_params":{},"user_consume_in_room":"0","user_send_gift_cnt_in_room":"0","individual_priority":"50","support_pin":"0","im_action":1,"forbidden_profile":false,"is_featured":"0","user_label":{"url_list":["http://p11-webcast.douyinpic.com/img/webcast/userlabel_regular_chat.png~tplv-obj.image"],"flex_setting_list":[],"text_setting_list":[],"uri":"","height":"0","width":"0","avg_color":"#E0BCD4","image_type":0,"open_web_url":"","is_animated":false}}}'
    # userBarrageMessage = DouyinMessageParser.parse_json(s)
    # print(json.dumps(userBarrageMessage.dict(), ensure_ascii=False))

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
