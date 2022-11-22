import re
import time
import datetime
import json
import copy
import random
import os

from amiyabot import PluginInstance
from core.util import read_yaml
from core import log, Message, Chain
from core.database.user import User, UserInfo
from core.database.bot import OperatorConfig
from core.resource.arknightsGameData import ArknightsGameData, ArknightsGameDataResource, Operator

curr_dir = os.path.dirname(__file__)

class WifuPluginInstance(PluginInstance):
    def install(self):
        pass

bot = WifuPluginInstance(
    name='每日随机助理',
    version='1.2',
    plugin_id='amiyabot-arknights-hsyhhssyy-wifu',
    plugin_type='',
    description='每日生成一个随机助理',
    document=f'{curr_dir}/README.md'
)

def compare_date_difference(day1: str,day2: str):
    time_array1 = time.strptime(''.join(day1.split(' ')[0]), "%Y-%m-%d") 
    timestamp_day1 = int(time.mktime(time_array1))
    time_array2 = time.strptime(''.join(day2.split(' ')[0]), "%Y-%m-%d")
    timestamp_day2 = int(time.mktime(time_array2))
    result = (timestamp_day1 - timestamp_day2) // 60 // 60 // 24
    return result


def compare_second_difference(day1: str,day2: str):
    time_array1 = time.strptime(''.join(day1.split(' ')[0]), "%Y-%m-%d %H:%M:%S") 
    timestamp_day1 = int(time.mktime(time_array1))
    time_array2 = time.strptime(''.join(day2.split(' ')[0]), "%Y-%m-%d %H:%M:%S")
    timestamp_day2 = int(time.mktime(time_array2))
    result = (timestamp_day1 - timestamp_day2)
    return result

async def wifu_action(data: Message):

    # log.info('触发了选老婆功能.')
    wifu_meta: dict = UserInfo.get_meta_value(data.user_id,'amiyabot-arknights-wifu')

    now = datetime.date.today()

    #查看User是不是已经有Wifu了
    if wifu_meta.__contains__('wifu_date') and wifu_meta.__contains__('wifu_name'):        
        # 计算日期
        last_wifu_time = wifu_meta['wifu_date']
        time_delta = compare_date_difference(now.strftime("%Y-%m-%d"),last_wifu_time)

        if time_delta<1 :            
            log.info(f'选老婆TimeDelta{time_delta}')
            return await show_existing_wifu(data,data.user_id)           

    wifu_meta['wifu_date'] = now.strftime("%Y-%m-%d")


    # 随机一位 Wifu给他
    operators = {}
    if not operators:
        operators = copy.deepcopy(ArknightsGameData().operators)

    operator = operators.pop(random.choice(list(operators.keys())))

    while OperatorConfig.get_or_none(operator_name=operator.name,operator_type=8):
        operator = operators.pop(random.choice(list(operators.keys())))

    wifu_meta['wifu_name'] = operator.name

    UserInfo.set_meta_value(data.user_id,'amiyabot-arknights-wifu',wifu_meta)

    ask = Chain(data, at=True).text(f'博士，您今日选到的助理是干员{operator.name}呢！').text('\n')
 
    return  await create_ret_data(data, ask,operator)

async def create_ret_data(data, ask,operator):
    
    skin = random.choice(operator.skins())
    skin_path = await ArknightsGameDataResource.get_skin_file(skin)

    if not skin_path:
        return ask.text('目前还没有该干员的立绘，真是抱歉博士~[face:9]')
    else:
        ask.image(skin_path)

    voices = operator.voices()
    if not voices:
        log.info(f'No voice file for operator {operator.operator_name}.')
        return ask
    else:
        voice = voices[0]
        voice_path = await ArknightsGameDataResource.get_voice_file(operator, voice['voice_title'],'_cn')


        if not voice_path:
            return ask
        else:
            ask.text(voice['voice_text'].replace('{@nickname}',data.nickname)).voice(voice_path)

    return ask

async def show_existing_wifu(data: Message, user_id: int):

    wifu_meta: dict = UserInfo.get_meta_value(user_id,'amiyabot-arknights-wifu')

    operator_name = wifu_meta['wifu_name']

    operators = {}
    if not operators:
        operators = copy.deepcopy(ArknightsGameData().operators)

    operator = operators[operator_name]

    ask = Chain(data, at=True).text(f'博士，您今天已经选过助理啦，您的助理是干员{operator.name}哦~ ')

    return await create_ret_data(data,ask,operator)

@bot.on_message(keywords=['选老婆', '抽老婆', '选助理', '抽助理'],level=2)
async def _(data: Message):
    return await wifu_action(data)