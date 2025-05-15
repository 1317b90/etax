import datetime
import json
import os
import time
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import Config
import get_invoice_code

# 发送消息给客户
def send_message(serviceid,userid,adminid,content,message_type="text"):
    # 如果是管理员或者群聊消息
    if adminid:
        userid=adminid

    # 如果是文本消息，并且不是管理员，则进行润色
    if message_type=="text" and not adminid:
        try:
            url=f"{Config.API_URL}/chat/polish?message={content}"
            response=requests.get(url)
            if response.status_code==200:
                content=response.json()["message"]
            else:
                print(f"请求润色失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"润色失败，错误: {e}")

    # 如果是文件，则发送到了群聊

    url = f"{Config.API_URL}/message/send"
    payload = {
        'serviceid':serviceid,
        'userid': userid,
        'type': message_type,
        'content': content,
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"消息发送成功，userid:{userid},content:{content}")
    else:
        print(f"请求失败: {response.text}")

# 将文件转为url
def up_file(file_path,file_name):
    url = f"{Config.API_URL}/file/"
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f)}
        response = requests.post(url, files=files)
        if response.status_code==200:
            return f"{Config.API_URL}/files/{file_name}"
        else:
            raise Exception("文件上传失败")

# 获取用户数据
def get_user_data(userid:str):
    url=f"{Config.API_URL}/user/{userid}"
    try:
        response=requests.get(url)
        # 检查响应状态码
        if response.status_code != 200:
            print(f"获取用户数据失败，状态码: {response.status_code}，响应: {response.text}")
            return None
        
        # 检查响应内容是否为空
        if not response.text:
            print(f"获取用户数据响应为空，userid: {userid}")
            return None
            
        # 尝试解析JSON
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求用户数据时出错: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"解析用户数据JSON时出错: {str(e)}，响应内容: {response.text}")
        return None


# 修改任务状态为进行中
def ing_task(id:str):
    url=f"{Config.API_URL}/task/ing"
    response=requests.get(url,params={"id":id})

    if response.status_code!=200:
        print(f"ingtask 失败：{response.text}")

# 修改任务状态为完成
def done_task(id:str,succeed:bool,msg:str=None,data:dict=None):
    url=f"{Config.API_URL}/task/done"
    data={"id":id,"succeed":succeed,"msg":msg,"data":data}
    response=requests.put(url,json=data)
    
    if response.status_code!=200:
        print(f"donetask 失败：{response.text}")


# 获取记忆
def get_memory(userid:str):
    key="memory_"+userid
    response=requests.get(f"{Config.API_URL}/redis/{key}")

    if response.status_code==200:
        response=response.json()
        response=json.loads(response.get("data","{}"))
        return response
    else:
        print(f"获取记忆失败：{response.text}")
        return {}

# 修改记忆
#key：开票信息 或 开票项目编码列表
def set_memory(userid:str,key:str,value):
    if isinstance(value,dict):
        value=json.dumps(value,ensure_ascii=False)
    memory_data=get_memory(userid)
    memory_data[key]=value
    memory_data=json.dumps(memory_data,ensure_ascii=False)
    data={"key":"memory_"+userid,"value":memory_data}
    response=requests.post(f"{Config.API_URL}/redis/",json=data)
    if response.status_code==200:
        return True
    else:
        print(f"修改记忆失败：{response.text}")
        return False

# 清空记忆
def clear_memory(userid:str):
    memory_data=get_memory(userid)

    if "开票信息" in memory_data:
        del memory_data["开票信息"]
    if "开票项目编码列表" in memory_data:
        del memory_data["开票项目编码列表"]

    data={"key":"memory_"+userid,"value":json.dumps(memory_data,ensure_ascii=False)}
    response=requests.post(f"{Config.API_URL}/redis/",json=data)
    if response.status_code==200:
        return True
    else:
        print(f"清空记忆失败：{response.text}")
        return False

# 发送邮件
def send_email(buy_email, file_path,file_name, invoice_name, seller_name):
    # 创建邮件对象
    msg = MIMEMultipart()
    msg['From'] = "wangrong@g4b.cn"
    msg['To'] = buy_email
    msg['Subject'] = f"关于{invoice_name}交易的发票已开具 - {seller_name}"

    # 邮件正文
    body = f"""
    您好！

    我是优帐通开票小助手，受{seller_name}委托，现将贵公司与{seller_name}关于{invoice_name}交易的正式发票发送给您。请您查收附件，并核对相关信息。

    顺祝商祺！

    优帐通开票小助手
    {time.strftime("%Y年%m月%d日 %H时%M分")}
    """
    msg.attach(MIMEText(body, 'plain'))

    # 附件
    with open(file_path, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=file_path)
        part['Content-Disposition'] = f'attachment; filename="{file_name}"'
        msg.attach(part)

    # 发送邮件

    with smtplib.SMTP_SSL("smtp.qiye.aliyun.com", 465) as server:
        server.login("wangrong@g4b.cn", "no36RlCgPQZzAVjA")
        server.send_message(msg)
    print("邮件发送成功")


# 使用AI查询编码
def ai_query_code(invoice_name:str,invoice_code_data:list=None ):
    if not invoice_code_data:
        invoice_code_data=get_invoice_code.main(invoice_name,is_image=False)
    url=f"{Config.API_URL}/chat/"
    messages=[
        {"role":"user","content":f"""
         # 流程：
         请在发票编码数据中，查询与商品`{invoice_name}`匹配的`code`
        # 注意：
        如果匹配成功，请直接返回`code`
        否则请返回`None`
        无需其他任何多余的描述
         # 发票编码数据
         {invoice_code_data}"""}
    ]
    response=requests.post(url,json={"messages":messages,"temperature":0.01})
    if response.status_code==200:
        result=response.json()
        if isinstance(result, str) and result.isdigit():
            return result
        return None
    else:
        print(f"AI查询编码失败：{response.text}")
        return None

if __name__ == "__main__":
    data=[
  {
    "code": "3070501000000000000",
    "name": "殡葬服务",
    "slv": "6%",
    "gjz": "",
    "zzstsgl": "免税",
    "flbmjc": "生活服务",
    "percent": "24.62%",
    "sm": "",
    "hzx": "N",
    "kyzt": "Y"
  },
  {
    "code": "1010113020000000000",
    "name": "鲜切花及花蕾",
    "slv": "9%",
    "gjz": "鲜切花、花蕾、康乃馨、满天星、勿忘我、玫瑰、情人草、紫罗兰、月季、香石竹、唐菖蒲、百合花、非洲菊、补血草、马蹄莲、火鹤",
    "zzstsgl": "",
    "flbmjc": "花卉",
    "percent": "22.20%",
    "sm": "包括康乃馨、满天星、勿忘我、玫瑰、情人草、紫罗兰、月季、香石竹、唐菖蒲、百合花、非洲菊、补血草、马蹄莲、火鹤、其他鲜切花及花蕾。",
    "hzx": "N",
    "kyzt": "Y"
  },
  {
    "code": "1060510090000000000",
    "name": "节庆庆典用品及相关娱乐用品",
    "slv": "13%",
    "gjz": "魔术道具、花彩、花环、人造雪、彩球、铃、圣诞树、圣诞树裙、布挂、圣诞球、圣诞彩灯、圣诞服、圣诞帽、圣诞头饰、圣诞背饰、翅膀、灯笼、拉花、挂花、贴花、气球、充气拱门",
    "zzstsgl": "",
    "flbmjc": "工艺品",
    "percent": "20.56%",
    "sm": "包括中西式节庆庆典娱乐活动用品，如魔术道具、花彩、花环等，以及用纸、金属箔、玻璃纤维等制成的人造雪、彩球、铃，化装舞会或中式节庆用面具及服装等各种节日用品",
    "hzx": "N",
    "kyzt": "Y"
  },
  {
    "code": "1060512100000000000",
    "name": "头发装饰用物品",
    "slv": "13%",
    "gjz": "梳子、橡胶梳、塑料梳、金属梳、牛角梳、木梳、发夹",
    "zzstsgl": "",
    "flbmjc": "日用杂品",
    "percent": "18.94%",
    "sm": "包括梳子、橡胶梳、塑料梳、金属梳、牛角梳、木梳、发夹",
    "hzx": "N",
    "kyzt": "Y"
  },
  {
    "code": "1060512110000000000",
    "name": "香水喷射器、粉扑及粉拍",
    "slv": "13%",
    "gjz": "香水喷射器、粉扑、粉拍、化妆喷雾器、座架、喷头",
    "zzstsgl": "",
    "flbmjc": "日用杂品",
    "percent": "13.67%",
    "sm": "",
    "hzx": "N",
    "kyzt": "Y"
  }
]
    name="梳子"
    print(ai_query_code(name,data))

