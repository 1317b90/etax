import random
import requests
import ddddocr
import json
from PIL import Image, ImageDraw, ImageFont

# 创建一个 session 对象，保持会话
session = requests.Session()
ocr = ddddocr.DdddOcr(show_ad=False)


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

cookies = {
    'Hm_lvt_e6205dc065614ddaf8f52688bf0d362c': '1746497403',
    'HMACCOUNT': 'B249702FC76484BC',
    'protalsid': 'c33940cb-81fb-4153-98f4-98e226172ca8',
    'Hm_lpvt_e6205dc065614ddaf8f52688bf0d362c': '1746497448'
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

def go(invoice_name:str):
    data = {
        "spmc":invoice_name,
        "ggxg":  "",
        "dw":  "",
    }

    yzm=get_yzm()
    if validate_yzm(yzm)=="success":
        data["validCode"]=yzm
        return get_data(data)
    else:
        return None

# 调用
def main(invoice_name:str,is_image=False):
    result=go(invoice_name)
    i=1
    while not result:
        if i>5:
            break
        print(f"第{i}次重试")
        result=go(invoice_name)
        i+=1

    if is_image:
        to_image(result)

    return result


# 转为图片
def to_image(data_list):
    # 设置表格样式
    padding = 10
    font_size = 24
    cell_height = 40
    
    # 设置表头和固定列宽
    headers = ['序号', '编号', '名称', '使用率']
    col_widths = [80, 270, 300, 100]  # 固定每列的宽度
    
    # 准备数据(添加序号)
    table_data = []
    for idx, item in enumerate(data_list, 1):
        table_data.append([
            str(idx), 
            item['code'], 
            item['name'], 
            item['percent']
        ])
        

    # 加载字体
    try:
        font = ImageFont.truetype("simhei.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # 创建临时图像和绘图对象用于计算文本宽度
    temp_image = Image.new('RGB', (1, 1), 'white')
    draw = ImageDraw.Draw(temp_image)
    

    # 计算图片总宽度
    width = sum(col_widths)
    height = cell_height * (len(table_data) + 1)  # +1 为表头行
    
    # 创建图片
    image = Image.new('RGB', (int(width), height), 'white')
    draw = ImageDraw.Draw(image)
    
    # 绘制表头
    x_offset = 0
    for i, header in enumerate(headers):
        draw.rectangle([x_offset, 0, x_offset + col_widths[i], cell_height], outline='black')
            # 直接绘制文本，不需要居中计算
        draw.text((x_offset + padding, padding), header, fill='black', font=font)
        x_offset += col_widths[i]
    
    # 绘制数据行
    for row_idx, row in enumerate(table_data, 1):
        y = row_idx * cell_height
        x_offset = 0
        for col_idx, cell in enumerate(row):
            draw.rectangle([x_offset, y, x_offset + col_widths[col_idx], y + cell_height], outline='black')
            # 直接绘制文本，不需要居中计算
            draw.text((x_offset + padding, y + padding), str(cell), fill='black', font=font)
            x_offset += col_widths[col_idx]

    # 指定保存路径
    save_path = "./files/table.png"
    image.save(save_path, format='PNG')


if __name__ == "__main__":
    print(main("公司年会礼品",is_image=True))
