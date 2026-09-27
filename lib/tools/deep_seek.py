
from openai import OpenAI

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger

client = None
# 检查是否参考了上下文
# deepSeekGet("The dog are moving.|They are moving.") #狗在移动。|他们在移动。
# deepSeekGet("They have a new house|They are moving.")# 他们有一栋新房子|他们要搬家了。
def deepSeekGet(aiPrompt,content):
    global client
    if client is None:
        client = OpenAI(api_key=configReader.getDeepseekKey(), base_url="https://api.deepseek.com")
    messages = [
        {
            "role": 'system',
            "content":
                f'{aiPrompt}'
        },
        {"role": "user", "content": content},
    ]
    logger.d("AI", messages)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    ret= response.choices[0].message.content
    logger.d("AI", ret)
    return ret
def deepseekSafe(aiPrompt,text):
    try:
        return deepSeekGet(aiPrompt,text)
    except Exception as e:
        logger.writeException()
        return