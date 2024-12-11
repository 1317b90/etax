import random
import requests
import ddddocr
import json
import xbot
from xbot import print, sleep
from .import package
from .package import variables as glv
import xbot_visual
# 创建一个 session 对象，保持会话
session = requests.Session()
ocr = ddddocr.DdddOcr()


# 设置 headers 和 cookies
headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
}

cookies = {
    'Hm_lvt_e6205dc065614ddaf8f52688bf0d362c': '1729841223,1730856675,1730942322',
    'HMACCOUNT': 'F136A6466231F07A',
    'Hm_lpvt_e6205dc065614ddaf8f52688bf0d362c': '1730942324',
    'protalsid': 'd1122a92-f619-4c49-8d9f-8c6f00e1c7ab',
}

# 将 cookies 加入 session
session.cookies.update(cookies)

def get_yzm():
    tmp=random.randint(100,999)
    # 获取验证码
    captcha_url = f'https://www.51fapiao.cn/serverapi/webServer/webapi/gencode?tmp={tmp}'
    response = session.get(captcha_url, headers=headers)

    # 检查验证码是否获取成功
    if response.status_code == 200:
        return ocr.classification(response.content)
    else:
        return None

def validate_yzm(yzm):
    # 验证验证码
    url = 'https://www.51fapiao.cn/serverapi/webServer/webapi/fpcx/checkYzm'
    data = {'yzm': yzm}
    response = session.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.text
    else:
        return None
    
def get_data(data:dict):
    url = "https://www.51fapiao.cn/serverapi/webServer/webapi/smartCode/queryGoodsCode"
     
    response = session.post(url, headers=headers, data=data, verify=False)

    
    if response.status_code == 200:
        try:
            respone=response.json()
        except:
            return None
        
        if respone.get('msg') == "queryByNameSuccess":
            return respone.get("data")
        else:
            return None
    
    else:
        return None

def go(spmc:str):
    data = {
        "spmc":spmc,
        "ggxg":  "",
        "dw":  "",
    }

    yzm=get_yzm()
    if validate_yzm(yzm)=="success":
        data["validCode"]=yzm
        return get_data(data)
    else:
        return None

# 测试
def main_(args):
    spmc="冰箱"
    result=go(spmc)

    i=1
    while not result:
        print(f"第{i}次重试")
        result=go(spmc)
        i+=1
        if i>2:
            break

    print(result)

# 调用
def main(args):
    result=go(glv["project_name"])
    i=1
    while not result:
        if i>5:
            break
        print(f"第{i}次重试")
        result=go( glv["project_name"])
        i+=1

    table_value= float(result[0]["percent"].strip('%'))

    # 根据阈值判断

    # 最大使用率大于阈值
    if table_value>float(glv["Threshold_value"]):
        # 直接使用最大使用率的编码
        glv["project_id"]=result[0]["code"]

    # 最大使用率小于阈值
    else:
        # 发送消息
        _ = xbot_visual.process.run(process="sendMsg", package=__name__, inputs={
            "Content": "编码不确定",
            "Type": "selectTable",
            "Data": json.dumps(result,ensure_ascii=False),
            }, outputs=[
        ], _block=("发送编码", 58, "调用流程"))

        # 主动报错，终止程序
        raise Exception("activeError")

