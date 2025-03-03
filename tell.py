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

# 发送消息给客户
def send_message(serviceid,userid,adminid,content,message_type="text"):
    # 如果是管理员或者群聊消息
    if adminid:
        userid=adminid

    # 如果是文本消息，并且不是管理员，则进行润色
    if message_type=="text" and not adminid:
        try:
            url=f"{Config.CHAT_URL}/polish?message={content}"
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

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"消息发送成功，userid:{userid},content:{content}")
    else:
        print(f"请求失败: {response.text}")

# 将文件转为url
def up_file(file_path,file_name):
    url = f"{Config.API_URL}/file"

    file_url=""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            response = requests.post(url, files=files)
            file_url=response.json()['url']
        
    except Exception as e:
        print(f"上传文件失败：{e}")
    return file_url    


# 获取用户数据
def get_user_data(userid:str):
    url=f"{Config.API_URL}/user/{userid}"
    response=requests.get(url)
    response_data=response.json()
    if "data" not in response_data.keys():
        raise Exception("该用户不存在")
    return response_data["data"]

# 修改任务状态为进行中
def ing_task(id:str):
    url=f"{Config.API_URL}/task/ing"
    response=requests.get(url,params={"id":id})

    if response.status_code!=200:
        print(f"ingtask 失败：{response.text}")

# 修改任务状态为完成
def done_task(id:str,succeed:bool,msg:str=None,data:dict=None):
    url=f"{Config.API_URL}/task/done"
    data={"id":id,"succeed":succeed,"msg":msg,"data":json.dumps(data)}
    response=requests.put(url,data=data)
    
    if response.status_code!=200:
        print(f"donetask 失败：{response.text}")


# 获取记忆
def get_memory(userid:str):
    params={"key":"memory_"+userid}
    response=requests.get(f"{Config.API_URL}/redis/value",params=params)

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
    response=requests.post(f"{Config.API_URL}/redis/value",json=data)
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
    response=requests.post(f"{Config.API_URL}/redis/value",json=data)
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


if __name__ == "__main__":
    send_email("1046711112@qq.com","./files/preview.jpg","测试的名称","tt发票","tt公司")
