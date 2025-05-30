import json
import os
import traceback
import re
import logging

import make_invoice 
import tell
import redis
import time
import get_invoice_code
import Config
import models

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("make_invoice")

# 创建 Redis 连接
def create_redis_connection():
    return redis.Redis(host=Config.REDIS_URL, port=Config.REDIS_DB, db=0)

r = create_redis_connection()

def main(data:models.Shell):
    try:
        # 将data转换为Execute格式 并执行开票
        make_invoice.main(models.Execute(**data.model_dump()))
    except Exception as e:
        error=str(e)
        if error=="开票完成":
            file_path="./files/invoice.pdf"
            file_name=f'{data.invoice_name}_金额_{data.invoice_amount}_{data.buy_name}_{time.strftime("%Y%m%d%H%M")}.pdf'
            file_url=tell.up_file(file_path,file_name)
            msg="开票已成功，请查收以下文件"

            # 发送邮件
            if data.buy_email:
                try:
                    tell.send_email(data.buy_email,file_path,file_name,data.invoice_name,data.company_name)
                    msg=f"开票已成功，发票文件已发送至您客户的邮箱 {data.buy_email}。请查收以下文件"
                except Exception as e:
                    tell.send_message(data.serviceid,data.userid,data.adminid,f"用户{data.userid}邮箱发送失败，错误：{str(e)}")

            # 上传成功了就把文件删掉
            os.remove(file_path)
            # 如果不是群聊，才反馈情况
            if not data.group_name:
                tell.send_message(data.serviceid,data.userid,data.group_name,msg)
            tell.send_message(data.serviceid,data.userid,data.group_name,file_url,"file")
            tell.done_task(data.taskid,True,"开票成功",{"url":file_url})
            tell.clear_memory(data.userid)

        elif error=="发票预览":
            file_name=f'{data.invoice_name}_金额_{data.invoice_amount}_{data.buy_name}_{time.strftime("%Y%m%d%H%M")}.jpg'
            file_url=tell.up_file("./files/preview.jpg",file_name)
            os.remove("./files/preview.jpg")
            tell.send_message(data.serviceid,data.userid,data.adminid,"您好！这是您发票的预览，请您确认一下是否存在问题。如果没问题，我将继续为您开具发票。感谢！")
            tell.send_message(data.serviceid,data.userid,data.adminid,file_url,"file")
            tell.done_task(data.taskid,True,"发票预览",{"url":file_url})

        elif error=="需查询编码":
            invoice_code_data=get_invoice_code.main(data.invoice_name,is_image=True)
            # 如果群聊，则不保存编码列表
            tell.set_memory(data.userid,"开票项目编码列表",invoice_code_data)
            file_url=tell.up_file("./files/table.png","table.png")
            os.remove("./files/table.png")
            tell.send_message(data.serviceid,data.userid,data.adminid,f"您的开票项目：#{data.invoice_name}，发票编码名称尚未确定。\n请您根据下表选择一个合适的编码名称，并将对应的序号或编码回复给我。感谢您的配合！")
            tell.send_message(data.serviceid,data.userid,data.adminid,file_url,"file")
            tell.done_task(data.taskid,False,"需查询编码",{"url":file_url})
            
        elif "登录失败：" in error:
            tell.send_message(data.serviceid,data.userid,data.adminid,"电子税务局网站登录失败了")
            tell.done_task(data.taskid,False,"登录失败",{"message":"登录失败"})
            tell.clear_memory(data.userid)

        # 重试 重试 重试 重试
        elif error == "多次登录失败" or "没有找到元素" in error or "超时" in error or "等待元素" in error or "等待页面" in error or "该元素没有位置及大小" in error:
            
            return error

        else:
            tell.send_message(data.serviceid,data.userid,data.adminid,"开票过程中出错了："+error)
            tell.done_task(data.taskid,False,"出错",{"message":error})
            tell.clear_memory(data.userid)
            logger.error(f"任务执行失败：{error}")


if __name__ == "__main__":
    logger.info("脚本已开启，接受开票任务中....")

    while True:
        # BRPOP 会阻塞直到队列中有任务
        try:
            task = r.brpop('make_invoice', timeout=30)
        except redis.TimeoutError:
            logger.warning("Redis连接超时")
        except redis.ConnectionError:
            logger.error("Redis连接错误")
            # 重新建立连接
            r = create_redis_connection()
            continue
        except redis.exceptions.ResponseError as e:
            logger.error(f"Redis响应错误: {e}")
            # 重新建立连接
            r = create_redis_connection()
            continue

        if task:
            # 初始化TIMEWAIT
            Config.TIMEWAIT=2
            data = task[1].decode('utf-8')  # 获取任务内容
            try:
                data = json.loads(data)
                # 修改任务状态为进行中
                tell.ing_task(data['taskid'])
                # 将开票信息存入记忆
                tell.set_memory(data['userid'],"开票信息",data)

                # 补充数据
                # 获取用户数据
                try:
                    user_data=tell.get_user_data(data['userid'])
                    if not user_data:  # 检查返回的数据是否为空
                        raise Exception("获取用户数据失败，返回为空")
                    if "admin" in data['userid']:
                        userid=user_data["puppet_id"]
                        if not userid:
                            raise Exception("未指代用户")
                        user_data=tell.get_user_data(userid)
                        if not user_data:  # 再次检查是否为空
                            raise Exception("获取指代用户数据失败，返回为空")

                    for key in ("uscid","dsj_username","dsj_password","company_name"):
                        data[key]=user_data[key]
                    data["sell_bank_name"]=user_data["bank_name"]
                    data["sell_bank_id"]=user_data["bank_id"]
                    # 将发票金额转为字符串，并移除可能存在的非数字字符（如"元"）
                    data["invoice_amount"] = re.sub(r'[^\d.]', '', str(data["invoice_amount"]))
                    # 如果是群聊，获取群聊名称
                    if data.get("is_group",False):
                        data["group_name"] = user_data["group_name"]
                except Exception as e:
                    raise Exception(f"获取用户数据时出错: {str(e)}")


                # 补充开票习惯
                try:
                    invoiceHabit=json.loads(user_data["invoice_habit"])
                    for key,value in invoiceHabit.items():
                        # 如果用户传入的值为空，则用习惯代替
                        if not data[key]:
                            data[key]=value
                except Exception as e:
                    logger.warning(f"习惯：{e}")
                logger.info(data)
                # 转换数据
                data = models.Shell(**data)

                # 执行主函数，最多重试三次
                result_sum=""
                result = main(data)
                for _ in range(Config.MAIN_RETRY):
                    # 出现重试，间隔10秒后重试
                    if result is not None:
                        result = main(data)
                        if result is not None:
                            result_sum += result
                            Config.wait()
                            Config.TIMEWAIT*=2
                            logger.warning(f"遇到错误：{result}，进行重试，当前等待时间：{Config.TIMEWAIT}秒")
                    else:
                        break

                if result is not None:
                    tell.send_message(data.serviceid,data.userid,data.adminid,"尊敬的用户，抱歉，由于电子税务局网络波动较大，多次尝试开票仍然失败。请您稍后大约10分钟再试，感谢您的理解与耐心！")
                    tell.done_task(data.taskid,False,"多次重试后失败",{"message":result_sum})
                    tell.clear_memory(data.userid)

            except Exception as e:
                try:
                    # 使用字典索引方式访问，而不是属性访问
                    if isinstance(data, dict):
                        tell.send_message(data['serviceid'], data['userid'], data['adminid'], "出现意外错误："+str(e))
                        tell.done_task(data['taskid'], False, "出错", {"message":str(e)})
                        tell.clear_memory(data['userid'])
                    else:
                        # 如果已经转换为对象，则使用属性访问
                        tell.send_message(data.serviceid, data.userid, data.adminid, "出现意外错误："+str(e))
                        tell.done_task(data.taskid, False, "出错", {"message":str(e)})
                        tell.clear_memory(data.userid)
                    traceback.print_exc()
                except Exception as e2:
                    logger.error(f"发送错误消息时出错: {str(e2)}")
                    traceback.print_exc()
        else:
            time.sleep(1)  # 等待1秒再继续
            #logger.debug(time.strftime("%Y-%m-%d %H:%M:%S"))