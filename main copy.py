# 导入
import random
import time
from DrissionPage import Chromium
import ddddocr

# 完成登录验证
def login_yzm(det,tab,is_save=False):
    # 获取验证码元素
    dialog_ele = tab.ele('@class=el-dialog__body')

    # 验证码背景
    yzm_eles = dialog_ele.eles('@tag()=img')

    move_x=0

    if len(yzm_eles) != 2:
        print('验证码获取失败')
        return False
    try:
        for i in range(len(yzm_eles)):
            # 获取验证码背景和缺口,最多等待十秒
            yzm_eles[i]=yzm_eles[i].src(timeout=10)

        if is_save:
            with open('./files/yzm_bg.jpg', 'wb') as f:
                f.write(yzm_eles[0])
            with open('./files/yzm_gap.png', 'wb') as f:
                f.write(yzm_eles[1])
        
        res = det.slide_match(yzm_eles[1],yzm_eles[0])
        move_x=res['target'][0]


        # 滑块按钮
        slider_ele = dialog_ele.ele('@class=slide-verify-slider-mask-item-icon')

        # 拖拽滑块
        slider_ele.drag(move_x, 0, random.uniform(0.5, 1.0))
    except Exception as e:
        print("验证码计算失败：",str(e))
        return False
       

    # 先查询是否存在警告
    message_ele=tab.ele('@class=el-message__content')
    if message_ele:
        raise Exception(message_ele.text)

    # 再次获取滑块按钮，最多等待2秒
    slider_ele = dialog_ele.ele('@class=slide-verify-slider-mask-item-icon',timeout=2)

    # 滑块按钮还在，说明验证失败
    if slider_ele:
        return False

    # 滑块按钮不在，说明验证成功
    else:
        return True



# ——————————登录————————————————————登录————————————————————登录————————————————————登录————————————————————登录————————————————————登录——————————
def login(det,tab,uscid,username,password,is_refresh=False):
    
        
    if is_refresh:
        # 刷新页面
        tab.refresh()
        # 等待页面加载完成
        tab.wait.load_start() 

    try:
        # 获取登录元素
        login_ele = tab.ele('@class=formContentE')
        # 获取登录元素中的表单元素
        login_ele = login_ele.ele('@class=el-form')
        input_eles = login_ele.eles('.el-input__inner') 

        input_content = (uscid,username,password)

        # 依次填写税号、账号、密码
        for i in range(len(input_eles)):
            # 输入内容
            input_eles[i].input(input_content[i])
            
        # 获取登录按钮
        login_button=login_ele.ele('@tag()=button')
        
        # 点击登录按钮
        login_button.click()

        # 尝试登录验证码
        # 如果验证码验证失败，再试一次
        if not login_yzm(det,tab):
            # 按ESC键退出
            tab.actions.key_down('Escape')
            
            # 然后再次点击登录按钮
            login_button.click()
            
            # 等待页面加载完成
            tab.wait.load_start() 
            # 如果第二次验证码验证失败，则登录失败
            if not login_yzm(det,tab):
                return False
        # 验证成功
        else:
            return True

    except Exception as e:
        print("登录失败：",str(e))
        return False


if __name__ == "__main__":
    uscid = "1234567890"
    username = "1234567890"
    password = "1234567890"
    
    # ——————————加载页面————————————————————加载页面————————————————————加载页面————————————————————加载页面————————————————————加载页面——————————
    # 连接浏览器
    browser = Chromium()  
    # 获取标签页对象
    tab = browser.latest_tab  
    # 访问网页
    tab.get('https://etax.guangdong.chinatax.gov.cn:8443/')  
    # 获取文本框元素对象
    ele = tab.ele('@class=loginBtnText')

    ele.click()

    # 等待页面加载完成
    tab.wait.load_start() 

    # ——————————登录————————————————————登录————————————————————登录————————————————————登录————————————————————登录————————————————————登录——————————
    det = ddddocr.DdddOcr(det=False, ocr=False)

    login_i=0
    # 尝试登录，最多尝试3次
    while login_i<3:
        # 如果是第一次登录，不刷新页面
        if login_i==0:
            is_refresh=False
        # 如果不是第一次登录，刷新页面
        else:
            is_refresh=True

        # 如果登录成功了，退出循环
        if login(det,tab,uscid,username,password,is_refresh):
            break
        # 如果登录失败了，刷新页面，重新登录
        else:
            login_i+=1
    
    if login_i==3:
        print("登录失败")
        exit()
            
    # 获取登录结果
    
            