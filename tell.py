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


def send_message(recipient,content,type="text"):

    url = f"{Config.API_URL}/redis/message"
    payload = {
        'key':"make_invoice_message",
        'type': type,
        'recipient': recipient,
        'content': content,
    }

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"消息发送成功，recipient:{recipient},content:{content}")
    else:
        print(f"请求失败，状态码: {response.status_code}")

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



# 使用手机号搜索对应的任务输入数据
def get_task_data(phone:str):
    params={"key":"make_invoice_"+phone}
    response=requests.get(f"{Config.API_URL}/redis/value",params=params)

    if response.status_code==200:
        response=response.json()
        response=json.loads(response.get("data",{}))
        return response
    else:
        print(f"get_task_data 失败：{response.text}")
        return {}
    
# 修改任务数据
def set_task_data(phone:str,data:dict):
    data={"key":"make_invoice_"+phone,"value":json.dumps(data)}
    response=requests.post(f"{Config.API_URL}/redis/value",json=data)
    if response.status_code==200:
        return True
    else:
        print(f"set_task_data 失败：{response.text}")
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
