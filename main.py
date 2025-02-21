import json
import os
import traceback

import make_invoice 
import tell
import redis
import time
import get_invoice_code
import Config

# 创建 Redis 连接
r = redis.Redis(host=Config.REDIS_URL, port=Config.REDIS_DB, db=0)

def main(data:dict):    
    try:
        make_invoice.main(**data)
        
    except Exception as e:
        error=str(e)
        if error=="开票完成":
            file_path="./files/invoice.pdf"
            file_name=f'{data["invoice_name"]}_金额_{data["invoice_amount"]}_{data["buy_name"]}_{time.strftime("%Y%m%d%H%M")}.pdf'
            file_url=tell.up_file(file_path,file_name)
            msg="开票已成功，请查收以下文件，如有任何问题，请随时联系我。"

            # 发送邮件
            if data.get("buy_email","")!="":
                try:
                    tell.send_email(data['buy_email'],file_path,file_name,data["invoice_name"],data['company_name'])
                    msg=f"开票已成功，发票文件已发送至您客户的邮箱 {data['buy_email']}。请查收以下文件，如有任何问题，请随时联系我。"
                except Exception as e:
                    tell.send_message(data["serviceid"],"admin_flx",f"用户{data['userid']}邮箱发送失败，错误：{str(e)}")

            # 上传成功了就把文件删掉
            os.remove(file_path)
            tell.send_message(data["serviceid"],data['userid'],msg)
            tell.send_message(data["serviceid"],data['userid'],file_url,"file")
            tell.done_task(data["taskid"],True,"开票成功",file_url)
            tell.clear_memory(data["userid"])

        elif error=="发票预览":
            file_name=f'{data["invoice_name"]}_金额_{data["invoice_amount"]}_{data["buy_name"]}_{time.strftime("%Y%m%d%H%M")}.jpg'
            file_url=tell.up_file("./files/preview.jpg",file_name)
            os.remove("./files/preview.jpg")
            tell.send_message(data["serviceid"],data['userid'],"您好！这是您发票的预览，请您确认一下是否存在问题。如果没问题，我将继续为您开具发票。感谢！")
            tell.send_message(data["serviceid"],data['userid'],file_url,"file")
            tell.done_task(data["taskid"],True,"发票预览",file_url)

        elif error=="需查询编码":
            invoice_code_data=get_invoice_code.main(data['invoice_name'],is_image=True)
            tell.set_memory(data['userid'],"开票项目编码列表",invoice_code_data)
            file_url=tell.up_file("./files/table.png","table.png")
            os.remove("./files/table.png")
            tell.send_message(data["serviceid"],data['userid'],f"您的开票项目：#{data['invoice_name']}，发票编码名称尚未确定。\n请您根据下表选择一个合适的编码名称，并将对应的序号或编码回复给我。感谢您的配合！")
            tell.send_message(data["serviceid"],data['userid'],file_url,"file")
            tell.done_task(data["taskid"],False,"需查询编码",file_url)
            
        elif "登录失败：" in error:
            tell.send_message(data["serviceid"],data['userid'],"电子税务局网站登录失败了")
            tell.done_task(data["taskid"],False,"登录失败",data['wecome_phone'])
            tell.clear_memory(data["userid"])

        # 重试 重试 重试 重试
        elif error == "多次登录失败" or "没有找到元素" in error or "超时" in error or "等待元素" in error or "等待页面" in error or "该元素没有位置及大小" in error:
            
            return error

        else:
            tell.send_message(data["serviceid"],data['userid'],"开票过程中出错了："+error)
            tell.done_task(data["taskid"],False,"出错",error)
            tell.clear_memory(data["userid"])
            print(f"任务执行失败：{error}")


if __name__ == "__main__":
    print("脚本已开启，接受开票任务中....")

    while True:
        # BRPOP 会阻塞直到队列中有任务
        try:
            task = r.brpop('make_invoice', timeout=30)
        except redis.TimeoutError:
            print("BRPOP timed out")
        except redis.ConnectionError:
            print("Connection error")

        if task:
            task_data = task[1].decode('utf-8')  # 获取任务内容
            print(time.strftime("%Y-%m-%d %H:%M:%S"))

            try:
                task_data = json.loads(task_data)
            except:
                print("输入数据解析失败",task_data)
                continue

            # 修改任务状态为进行中
            tell.ing_task(task_data["taskid"])
            # 将开票信息存入记忆
            tell.set_memory(task_data["userid"],"开票信息",task_data)

            try:
                # 补充数据
                task_data=tell.supplementary_data(task_data["userid"],task_data)
                # 执行主函数，最多重试三次
                result_sum=""
                result = main(task_data)
                for _ in range(Config.MAIN_RETRY):
                    # 出现重试，间隔10秒后重试
                    if result is not None:
                        result = main(task_data)
                        if result is not None:
                            result_sum += result
                            Config.wait()
                            Config.TIMEWAIT*=1.3
                            print(f"遇到错误：{result}，进行重试，当前等待时间：{Config.TIMEWAIT}秒")
                    else:
                        break
                    
                if result is not None:
                    tell.send_message(task_data["serviceid"],task_data['userid'],"尊敬的用户，抱歉，由于电子税务局网络波动较大，多次尝试开票仍然失败。请您稍后大约10分钟再试，感谢您的理解与耐心！")
                    tell.done_task(task_data["taskid"],False,"多次重试后失败",result_sum)
                    tell.clear_memory(task_data['userid'])

            except Exception as e:
                tell.send_message(task_data["serviceid"],task_data['userid'],"出现意外错误："+str(e))
                tell.done_task(task_data["taskid"],False,"出错",str(e))
                tell.clear_memory(task_data['userid'])
                traceback.print_exc()
        else:
            print(time.strftime("%Y-%m-%d %H:%M:%S"))