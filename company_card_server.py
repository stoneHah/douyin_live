import threading

from dotenv import load_dotenv
from langchain import LLMChain
from langchain.callbacks.manager import CallbackManager
from langchain.chat_models import ChatOpenAI
from langchain.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional

from sse_starlette import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware

from custom_callback import StreamingLLMCallbackHandler, StreamTokenBuffer

load_dotenv()


class CompanyCard(BaseModel):
    id: Optional[int] = Field(None, description="唯一ID")
    company_name: str = Field(..., description="企业名称")
    company_intro: str = Field(..., description="公司简介")
    social_media_account: str = Field(..., description="社交媒体账号")
    production_type: str = Field(..., description="生产类型/产品类型")
    target_audience: str = Field(..., description="目标受众/客户群体")
    company_feature: str = Field(..., description="公司特色/优势")
    company_philosophy: str = Field(..., description="公司理念")
    company_history: str = Field(..., description="公司历史")
    business_scope: str = Field(..., description="公司业务范围")
    audience_group: str = Field(..., description="受众群体")


from fastapi import FastAPI, HTTPException, Query, Request
import json
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "company_data.json"


def get_next_id(data):
    ids = [card["id"] for card in data if "id" in card]
    if ids:
        return max(ids) + 1
    return 1


# 获取所有企业名片
@app.get("/cards/", tags=["Cards"], description="获取所有企业名片")
def get_cards():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return []


# 增加一个企业名片
@app.post("/cards/", tags=["Cards"], description="增加一个企业名片")
def add_card(card: CompanyCard):
    data = []
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        pass

    card.id = get_next_id(data)
    data.append(card.dict())
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)
    return {"status": "Card added successfully", "id": card.id}


# 根据ID获取企业名片信息
@app.get("/cards/{card_id}", tags=["Cards"], description="根据ID获取企业名片信息")
def get_card_by_id(card_id: int):
    data = []
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Card not found")

    for existing_card in data:
        if existing_card["id"] == card_id:
            return existing_card
    raise HTTPException(status_code=404, detail="Card not found")


# 修改一个企业名片
@app.put("/cards/{card_id}", tags=["Cards"], description="根据ID更新企业名片")
def update_card(card_id: int, card: CompanyCard):
    data = []
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Card not found")

    for i, existing_card in enumerate(data):
        if existing_card["id"] == card_id:
            card.id = card_id
            data[i] = card.dict()
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f)
            return {"status": "Card updated successfully"}
    raise HTTPException(status_code=404, detail="Card not found")


# 删除一个企业名片
@app.delete("/cards/{card_id}", tags=["Cards"], description="根据ID删除企业名片")
def delete_card(card_id: int):
    data = []
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Card not found")

    for i, existing_card in enumerate(data):
        if existing_card["id"] == card_id:
            del data[i]
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f)
            return {"status": "Card deleted successfully"}
    raise HTTPException(status_code=404, detail="Card not found")


roles_and_responsibilities = {
    "ad_planning": {
        "role": "广告策划",
        "responsibility": "负责制定广告宣传的策略和方向，确定目标受众和宣传内容。"
    },
    "copy_planning": {
        "role": "文案策划",
        "responsibility": "负责撰写广告文案，制作宣传语、广告词和宣传口号，以及其他文字性宣传内容。"
    },
    "ad_marketing_manager": {
        "role": "广告营销经理",
        "responsibility": "负责监控和管理广告的投放和推广，制定广告投放策略，确保广告达到预期效果。"
    },
    "operation": {
        "role": "运营",
        "responsibility": "协助各个岗位的工作，负责沟通协调、文件管理、进度控制等工作，以确保广告制作的顺利进行。"
    },
    "project_leader": {
        "role": "项目负责人",
        "responsibility": "则更加关注整个项目的规划、组织和管理。"
    }
}

entries_data = [
    {'id': 1, 'entry': '脚本的创作', 'roles': ['ad_planning', 'copy_planning'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，完成以下工作: 

1、写一份吸引观众兴趣，引发情感共鸣的脚本
2、写一份增加产品销量的脚本
3、写一份突出企业形象的脚本

要求脚本描述详细，确认镜头，出现时间，场景，出场所需要的道具，在最终的结果里不要体现你的角色信息。

{role_skills}

[企业名片]
{company_info}
                """},
    {'id': 2, 'entry': '短视频的运营', 'roles': ['operation'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，完成以下工作:
1、写一份吸引[受众人群]的运营文案
2、写一份增加视频的曝光度的运营文案

{role_skills}

[受众人群]
{audience_group}

[企业名片]
{company_info}
                     """
     },
    {'id': 3, 'entry': '广告的策划方案及具体操作流程', 'roles': ['ad_planning'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，写一份策划方案，在方案中包含如下几个因素:
 1、广告的投放时间和频率如何安排?
 2、是否需要考虑季节性或节日性的因素?
 3、产品或服务的独特卖点是什么?
 4、与竞争对手相比，有哪些优势?
 5、广告的创意是否能够吸引目标受众的注意力?
 6、是否与品牌形象和价值观相符合?
 7、广告的目标是什么?
 8、是增加销售量、提高品牌知名度还是宣传新产品?

 {role_skills}

 [企业名片]
 {company_info}
                          """
     },
    {'id': 4, 'entry': '短视频文案编辑', 'roles': ['copy_planning'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]和[受众人群]写一份短视频文案，文案内容和风格需要与[受众人群]相匹配，达到吸引观众的效果。

{role_skills}

[受众人群]
{audience_group}

[企业名片]
{company_info}
   """
     },
    {'id': 5, 'entry': '种草文案', 'roles': ['copy_planning'],
     'scripts': """
我想要你扮演{roles_desc}的角色，根据我的[企业名片]，完成以下工作:
1、写一份突出产品功效或效果的种草文案
2、写一份突出产品性价比的种草文案

## 种草文案
种草文案是一种旨在推广某种产品或服务的文案，旨在引发观众的购买兴趣和欲望。以下是一些编写种草文案的要点：
● 引起兴趣：开篇的种草文案需要引起读者的兴趣。可以使用引人入胜的问题、吸引人的事实或独特的描述来吸引注意力。
例：你曾经想过用一款令人惊艳的口红彻底改变你的妆容吗？

● 强调产品特点和优势：在文案中突出产品的特点和优势，让读者对其产生兴趣。强调独特的功能、高品质的材料或创新的设计。
例：我们的口红不仅色彩饱满持久，而且含有滋润成分，让你的双唇持续滋润娇艳。

● 刻画使用场景和体验：通过描述产品的使用场景和使用体验，让读者能够想象自己拥有该产品的感受。将产品的特性与实际情境结合起来，激发读者的想象力。
例：在约会前，轻轻涂抹上我们的口红，让你的微笑更加迷人，吸引你心仪的对象。

● 提供真实案例或见证：通过分享真实的用户案例或见证，增加产品可信度和口碑效应。展示其他人对产品的积极反馈和成果，让读者更有信心购买。
例：我朋友使用了这款口红后，她每天都收到很多赞美的目光，真的好好看！

● 优惠和限时促销：如果有优惠和限时促销活动，可以在文案中强调，以鼓励读者尽快行动。
例：现在购买口红，享受半价优惠，在有限的时间内抓住机会！

● 呼吁行动和购买：在文案的结尾，明确呼吁读者采取行动，并引导他们前往购买产品的地方。
例：不要再犹豫了，现在就点击购买，享受更美丽的妆容！

总结起来，种草文案的编写需要引起兴趣、强调产品特点和优势、刻画使用场景和体验，并提供真实案例和见证。同时，如果有优惠和限时促销活动，也需要强调。最后，在文案的结尾呼吁行动和购买，引导读者前往购买页面。

{role_skills}

[企业名片]
{company_info}
                                    """
     },
    {'id': 6, 'entry': '产品测评方案', 'roles': ['copy_planning', 'ad_planning'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，写一份关于产品的测评文案。
                         
 ## 产品测评方案
 产品测评方案是评估产品性能和质量的计划和方法。以下是一个典型的产品测评方案的步骤：
    1、确定测评目标：明确测评的目的和时间范围，确定需要评估的产品特征和指标。
    2、设计测评方案：选择适当的测评方法和工具，包括实验室测试、用户调查、专家评估等，制定测评的步骤和流程。
    3、准备测试环境和设备：确保测试环境符合测评要求，准备必要的设备和工具，确保测试过程的准确性和可靠性。
    4、进行产品测评：按照测评方案进行实际测试和评估，收集数据和反馈意见。
    5、数据分析和结果展示：对测试数据进行分析和比较，制作测评报告，展示产品性能和质量的评估结果。
    6、结论和建议：总结测评结果，提出改进建议和优化方案，帮助产品改进和优化。
    7、审查和验证：经过改进后的产品进行再次测评，确保改进方案的有效性和实施结果。
    8、定期跟踪和更新：持续跟踪产品的表现和用户反馈，及时更新产品测评方案和方法，保持测评工作的持续性和准确性。
    以上是一个通用的产品测评方案的步骤，具体的方案可以根据产品类型和评估目标进行调整和定制。

{role_skills}

[企业名片]
{company_info}
                                         """
     },
    {'id': 7, 'entry': '产品的核心卖点', 'roles': ['ad_marketing_manager', 'project_leader', 'ad_planning'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，写一份关于产品的核心卖点。

## 产品的核心卖点
  产品的核心卖点是指产品所具备的最重要、最吸引人的特点、优势或功能，这些特点能够满足消费者的需求，并且能够与竞争对手相比具有明显的优势。核心卖点通常是消费者购买该产品的主要决策依据。

以下是一些常见的产品核心卖点：

● 高品质：产品具有出色的质量和可靠性，能够提供长期稳定的性能。
● 创新性：产品具备全新的设计、技术或功能，能够满足消费者对新鲜、独特的需求。
● 效能和效果：产品能够提供非常好的性能和结果，能够解决消费者的需求或问题。
● 方便性：产品使用方便，能够简化消费者的生活，节省时间和精力。
● 成本效益：产品提供较低的价格，相对于竞争对手来说具有更高的性价比。
● 个性化定制：产品能够根据消费者的个性需求进行定制，提供个性化的体验。
● 环保和可持续性：产品对环境友好，并且具备可持续性的特性，符合现代消费者的关注点。
产品的核心卖点应该根据目标市场需求和竞争分析来确定，以确保产品能够满足消费者的期望并获得竞争优势。

 {role_skills}

 [企业名片]
 {company_info}
                                              """
     },
    {'id': 8, 'entry': '产品目标市场分析以及内容创作', 'roles': ['ad_planning', 'copy_planning'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，对产品制定出一套有效的广告方案。

当进行广告策划时，您可以按照以下步骤进行：

1、确定目标受众：了解你的产品或服务适合什么样的受众群体，并确定你的广告将针对哪个具体的受众群体。
2、设定广告目标：明确广告的目标，是增加品牌知名度、促进销售、提高转化率还是其他目标。
3、研究竞争对手：了解竞争对手的广告策略和市场定位，以便制定一种能与他们区分开的广告策略。
4、确定品牌定位：根据你的产品或服务的特点，确定你的品牌在广告中的定位和核心信息。
5、制定广告策略：根据目标受众和品牌定位，确定广告的内容、呈现方式、传播渠道等。
6、设计创意和内容：制作广告素材，包括图片、视频、文案等，确保广告内容吸引人且能让受众记住。
7、选择媒体渠道：根据目标受众的使用习惯和广告预算选择合适的媒体渠道，如电视、广播、印刷媒体、社交媒体等。
8、设置广告预算：确定广告策划所需的预算，并确定在不同媒体渠道上的投放比例。
9、监测和优化：定期监测广告效果，根据数据反馈进行优化，确保广告策略的有效性和持续改进。
通过按照以上步骤进行广告策划，您将能够制定出一套有效的广告方案，并吸引目标受众的关注和兴趣，从而提高品牌的知名度和销售业绩。

{role_skills}

[企业名片]
{company_info}
                                       """
     },
    {'id': 9, 'entry': '广告剧本的创作模板', 'roles': ['copy_planning'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，写一份广告剧本。
     
## 剧本需要按照下面的约束来展开

[开场白] 欢迎收看我们的广告剧本创作模板！在这个模板中，我们将为您提供一种通用的创作模式，帮助您快速构思和编写一份吸引人的广告剧本。

[场景设定] 首先，让我们确定广告的背景和场景。这包括确定广告发生的地点、时间，以及与广告相关的环境和细节。请确保这些设定与您的产品或服务的特点相符，以确保广告的一致性和有效性。

[故事情节] 接下来，让我们构思一个有趣又引人入胜的故事情节。您可以选择一种情感或故事的线索，以激发观众的共鸣。确保您的故事情节能够突显出您的产品或服务的特色，并使观众对其感兴趣。

[角色介绍] 现在，让我们介绍一些具有代表性的角色。为广告创作一些有个性和吸引力的角色，以便观众能够与他们产生共鸣。这些角色可以是使用您的产品或服务的现实生活中的人，或者是代表您品牌形象的虚构人物。

[核心信息] 确保您在剧本中传递出您的核心信息。这可能是您的产品或服务的主要优势，或者是您品牌的核心理念。将这些信息融入到角色的对话和行为中，以便观众能够直观地理解并记住它们。

[高潮和转折] 为了增加广告的趣味性和吸引力，我们推荐在剧本中添加一些高潮和转折点。这些可以是角色的意外发现、问题的解决，或者是一种突如其来的情境转变。这些元素将为观众带来惊喜和愉悦，并增加广告的吸引力。

[结尾] 最后，为您的广告剧本设计一种引人注目的结尾。这可以是一个有趣的点子、一句引人深思的台词，或者是一种突出您品牌形象的方式。确保结尾能够激发观众的兴趣和行动，并使他们对您的产品或服务保持长久的印象。

[结束语] 希望我们的广告剧本创作模板能给您提供一些启发和帮助！您可以根据自己的需求和创意进行修改和调整，以创作出最适合您的广告剧本。祝您创作成功！

{role_skills}

[企业名片]
{company_info}
                                """
     },
    {'id': 10, 'entry': '产品广告的市场营销以及宣传', 'roles': ['ad_marketing_manager', 'operation'],
     'scripts': """我想要你扮演{roles_desc}的角色，根据我的[企业名片]，对产品进行分析并写一份市场报告。

## Desc
 广告营销是一种宣传和推广产品或服务的策略和方法。它通过广告和营销活动来增加产品或服务的知名度、吸引消费者的注意力，从而促进销售和业务增长。以下是一些常见的广告营销策略：

目标市场分析：在开始广告营销之前，对目标市场进行深入的研究和分析是非常重要的。了解目标市场的需求、偏好和行为习惯可以帮助您更好地定位广告内容和选择合适的媒体渠道。
创意广告内容：创意广告内容是吸引消费者注意的关键。通过使用有趣、独特和引人注目的创意，您可以突出产品或服务的独特卖点，并在激烈的市场竞争中脱颖而出。
多渠道广告投放：选择合适的广告媒体渠道非常重要。您可以考虑在电视、广播、报纸、杂志和互联网等各种渠道进行广告投放，以覆盖更广泛的受众群体。
社交媒体广告：社交媒体已成为广告营销中不可或缺的一部分。通过在社交媒体平台上投放广告，您可以直接与目标受众互动，并提高品牌知名度和产品认知度。
优惠奖励和促销活动：提供优惠券、折扣、礼品或其他奖励可以吸引消费者购买您的产品或服务。促销活动还可以帮助您在竞争激烈的市场中脱颖而出，吸引更多的消费者购买。
口碑营销：消费者的口碑传播对于产品或服务的成功非常重要。通过提供优质的产品和卓越的客户服务，您可以获得顾客的好评和推荐，从而建立良好的口碑，为您的广告营销活动提供有力支持。

数据分析和追踪：通过使用数据分析工具，您可以追踪广告效果并了解消费者的反应。根据这些数据，您可以调整广告策略，优化广告投放，以获得更好的回报。

总之，广告营销是一个多方面的过程，需要您深入了解目标市场并使用创意和策略来吸引消费者。通过选择适合的媒体渠道、创造有吸引力的广告内容，并进行有效的市场推广活动，您可以提高产品或服务的知名度，吸引更多的消费者并实现销售增长。

{role_skills}

[企业名片]
{company_info}
                                     """
     }
]


@app.get("/entries/", tags=["Entries"], description="获取所有词条信息")
def get_entries_without_roles():
    return [{"id": entry["id"], "entry": entry["entry"]} for entry in entries_data]


class PromotionPlan(BaseModel):
    company_card_id: int = Field(..., description="企业名片id")
    entry_id: int = Field(..., description="词条id")

def generate_company_description(card: CompanyCard) -> str:
    card_text = "\n"
    card_text += f"企业名称：{card.company_name}\n"
    card_text += f"公司简介：{card.company_intro}\n"
    card_text += f"社交媒体账号：{card.social_media_account}\n"
    card_text += f"生产类型/产品类型：{card.production_type}\n"
    card_text += f"目标受众/客户群体：{card.target_audience}\n"
    card_text += f"公司特色/优势：{card.company_feature}\n"
    card_text += f"公司理念/核心价值观：{card.company_philosophy}\n"
    card_text += f"公司历史/发展：{card.company_history}\n"
    card_text += f"企业规模：100人\n"
    card_text += f"公司业务范围：{card.business_scope}\n"
    card_text += f"受众群体: {card.audience_group}"
    return card_text

@app.get("/gpt-scripts/{company_card_id}/{entry_id}", tags=["Promotion"], description="获取发送给GPT的脚本")
async def get_gpt_scripts(company_card_id: int, entry_id: int):
    entry = next(entry for entry in entries_data if entry["id"] == entry_id)
    # 根据roles获取roles_and_responsibilities对应的信息
    related_roles_info = {role_key: roles_and_responsibilities[role_key] for role_key in entry['roles']}
    roles_desc = "、".join([role_info["role"] for role_info in related_roles_info.values()])
    role_skills = ""
    for role_key, role_info in related_roles_info.items():
        role_skills += f"## {role_info['role']}\n"
        role_skills += "### skills\n"
        role_skills += f"    {role_info['responsibility']}\n\n"

    company_data = get_card_by_id(company_card_id)
    company_info = generate_company_description(CompanyCard(**company_data))


    return {'scripts': entry['scripts'].format(roles_desc=roles_desc, role_skills=role_skills, company_info=company_info,audience_group=company_data['audience_group'])}


class PromptRequest(BaseModel):
    prompt: str

enter_special_char = "|!Enter!|"

@app.get("/tt")
def print_thread_info():
    stream_handler = StreamingLLMCallbackHandler()
    print('threadid,stream_handler_id,bufferid', threading.current_thread().ident, hex(id(stream_handler)),hex(id(stream_handler.buffer)))


@app.post("/promotion_plan", tags=["Promotion"], description="获取推广方案")
async def chat_stream(request: Request, promptRequest: PromptRequest):

    stream_handler = StreamingLLMCallbackHandler()
    print('threadid,bufferid',threading.current_thread().ident,hex(id(stream_handler.buffer)))

    llm = ChatOpenAI(streaming=True, model_name='gpt-3.5-turbo',
                     callback_manager=CallbackManager([stream_handler]), verbose=True,
                     temperature=0.6)

    human_template = "{text}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([human_message_prompt])
    chain = LLMChain(
        llm=llm,
        prompt=chat_prompt
    )
    def query():
        resp = chain.run(promptRequest.prompt)
        # resp = llm_chain.predict(human_input=promptRequest.prompt)
        # resp = llm_chain([HumanMessage(content=str)])
        print(resp)

    t = threading.Thread(target=query)
    t.start()

    async def event_generator(stream_token_buffer: StreamTokenBuffer):
        for event,token in stream_token_buffer.stream_tokens():
            # If client closes connection, stop sending events
            if await request.is_disconnected():
                break

            print("event,data=", event, token)
            yield {
                "event": event,
                "data": token.replace("\n",enter_special_char)
                # "data": token
            }

    return EventSourceResponse(event_generator(stream_handler))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
