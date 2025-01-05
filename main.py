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
        tell.ing_task(data['task_id'])
        make_invoice.main(**data)
    except Exception as e:
        error=str(e)
        if error=="开票完成":
            file_path="./files/invoice.pdf"
            file_name=f'{data["invoice_name"]}_金额:{data["invoice_amount"]}_{data["buy_name"]}_{time.strftime("%Y%m%d%H%M")}.pdf'
            file_url=tell.up_file(file_path,file_name)
            msg="开票已成功，请查收以下文件，如有任何问题，请随时联系我。"

            # 发送邮件
            if data.get("buy_email","")!="":
                try:
                    tell.send_email(data['buy_email'],file_path,file_name,data["invoice_name"],data['company_name'])
                    msg=f"开票已成功，发票文件已发送至您客户的邮箱 {data['buy_email']}。请查收以下文件，如有任何问题，请随时联系我。"
                except Exception as e:
                    tell.send_message("admin_flx",str(e))

            # 上传成功了就把文件删掉
            os.remove(file_path)
            tell.send_message(data['wecome_id'],msg)
            tell.send_message(data['wecome_id'],file_url,"file")
            tell.done_task(data['task_id'],True,"开票成功",file_url)
            tell.set_task_data(data['wecome_id'],{})

        elif error=="发票预览":
            file_name=f'{data["invoice_name"]}_金额:{data["invoice_amount"]}_{data["buy_name"]}_{time.strftime("%Y%m%d%H%M")}.jpg'
            file_url=tell.up_file("./files/preview.jpg",file_name)
            os.remove("./files/preview.jpg")
            tell.send_message(data['wecome_id'],"您好！这是您发票的预览，请您确认一下是否存在问题。如果没问题，我将继续为您开具发票。感谢！")
            tell.send_message(data['wecome_id'],file_url,"file")
            tell.done_task(data['task_id'],True,"发票预览",file_url)

        elif error=="需查询编码":
            invoice_code_data=get_invoice_code.main(data['invoice_name'],is_image=True)

            invoice_data=tell.get_task_data(data['wecome_id'])
            invoice_data['table']=invoice_code_data
            tell.set_task_data(data['wecome_id'],invoice_data)
            file_url=tell.up_file("./files/table.png","table.png")
            os.remove("./files/table.png")
            tell.send_message(data['wecome_id'],f"您的开票项目：#{data['invoice_name']}，发票编码名称尚未确定。\n请您根据下表选择一个合适的编码名称，并将对应的序号或编码回复给我。感谢您的配合！")
            tell.send_message(data['wecome_id'],file_url,"file")
            tell.done_task(data['task_id'],False,"需查询编码",file_url)
            
        elif "登录失败：" in error:
            tell.send_message(data['wecome_id'],"登录失败了")
            tell.done_task(data['task_id'],False,"登录失败",data['wecome_phone'])
            tell.set_task_data(data['wecome_id'],{})

        # 重试 重试 重试 重试
        elif error == "多次登录失败" or "没有找到元素" in error or "超时" in error or "等待元素" in error or "等待页面" in error or "该元素没有位置及大小" in error:
            
            return error

        else:
            tell.send_message(data['wecome_id'],"出错了："+error)
            tell.done_task(data['task_id'],False,"出错",error)
            tell.set_task_data(data['wecome_id'],{})
            print(f"任务执行失败：{error}")


if __name__ == "__main__":
    for i in range(0x1f600,0x1f650):
        print(chr(i),end=" ")
        if i%16==15:
            print()

    while True:
        # BRPOP 会阻塞直到队列中有任务
        task = r.brpop('make_invoice')
        if task:
            task_data = task[1].decode('utf-8')  # 获取任务内容
            print(time.strftime("%Y-%m-%d %H:%M:%S"))
            print(task_data)
            try:
                task_data = json.loads(task_data)
            except:
                print("输入数据解析失败",task_data)
                continue

            # 补充id，避免网站发起时出错
            task_data['wecome_id']=task_data.get("wecome_id","")
            task_data['task_id']=task_data.get("task_id","")

            try:
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
                            Config.TIMEWAIT*=2
                            print(f"遇到错误：{result}，进行重试，当前等待时间：{Config.TIMEWAIT}秒")
                    else:
                        break
                    
                if result is not None:
                    tell.send_message(task_data['wecome_id'],"尊敬的用户，抱歉，由于电子税务局网络波动较大，多次尝试开票仍然失败。请您稍后大约10分钟再试，感谢您的理解与耐心！")
                    tell.done_task(task_data['task_id'],False,"多次重试后失败",result_sum)
                    tell.set_task_data(task_data['wecome_id'],{})

            except Exception as e:
                tell.send_message(task_data['wecome_id'],"出错："+str(e))
                tell.done_task(task_data['task_id'],False,"出错",str(e))
                tell.set_task_data(task_data['wecome_id'],{})
                traceback.print_exc()
