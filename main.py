# 导入
import random
import time
from DrissionPage import Chromium
import ddddocr
import Error
from DrissionPage.common import Settings
from DrissionPage.common import Keys

#设置找不到元素时，抛出异常
Settings.raise_when_ele_not_found = True
#设置点击失败时，抛出异常
Settings.raise_when_click_failed = True
#设置等待失败时，抛出异常
Settings.raise_when_wait_failed = True
#设置单例化标签页对象
Settings.singleton_tab_obj = True


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
    slider_ele.drag(move_x, 0, random.uniform(0.3, 0.8))

    # 先查询是否存在警告
    try:
        message_ele=tab.ele('@class=el-message__content',timeout=2)
        raise Error.LoginError(message_ele.text)
    except:
        pass


    # 不报错，说明按钮存在，则没通过验证
    try:
        dialog_ele.ele('@class=slide-verify-slider-mask-item-icon',timeout=1)
        return False
    except:
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
            return False
        
        # 验证成功
        else:
            return True

    except Exception as e:
        # 判断是否为指定的登录错误
        if isinstance(e, Error.LoginError):
            raise e
        # 如果是其他的错误，重试就可以了
        else:
            print("登录失败：",str(e))
            return False


if __name__ == "__main__":
    uscid = "91440101MA5CR0FL12"
    username = "13922232205"
    password = "Xia3331068."
    invoice_type="普通发票"
    # invoice_type="增值税专用发票"
    is_person=True

    # 购买方信息
    buy_name="张三"
    buy_id="1234567890"
    buy_address="广州市天河区"
    buy_phone="13922232205"
    buy_bank_name="中国银行"
    buy_bank_id="1234567890"

    # 销售方信息
    sell_bank_name="中国银行"
    sell_bank_id="1234567890"


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

    MAX_LOGIN_ATTEMPTS = 8
    
    for attempt in range(MAX_LOGIN_ATTEMPTS):
        # 第一次登录不刷新页面，后续登录需要刷新
        is_refresh = attempt > 0
        
        if login(det, tab, uscid, username, password, is_refresh):
            break
    else:
        raise Exception("多次登录失败")
    
    # 

    # 登录成功了，点击办税员
    # dialog_ele = tab.ele('.el-dialog')

    radio_group_ele = tab.ele('@class=el-radio-group')
    riadio_label_eles=radio_group_ele.eles('.el-radio__label')

    for riadio_label_ele in riadio_label_eles:
        if riadio_label_ele.text == '办税员':
            riadio_label_ele.click()
            break
    else:
        raise Exception("没有找到办税员")

    # 接着点击确定
    tab.ele('tag:span@@text()=确认').click()

    tab.wait.load_start() 

    # 访问立即开票页面
    tab.get('https://dppt.guangdong.chinatax.gov.cn:8443/blue-invoice-makeout')

    tab.wait.load_start() 
    
    # 点击立即开票
    tab.wait.eles_loaded('.quick-entrance')
    quick_entrance_ele=tab.ele('@class=quick-entrance')
    quick_choose_ele=quick_entrance_ele.ele('@class=invoice-entrance-choose__content txc rdu2')
    quick_choose_ele.click()
    
    # 等待票类选择框出现
    tab.wait.eles_loaded('@class=t-dialog__body')

    # 按4次TAB，到选择票类
    for _ in range(4):
        tab.actions.key_down('TAB')

    if invoice_type == "普通发票":
        tab.actions.key_down('DOWN')
        tab.actions.key_down('DOWN')
    elif invoice_type == "增值税专用发票":
        tab.actions.key_down('DOWN')
        # 增值税发票不可选自然人
        is_person=False

    else:
        raise Exception("发票类型错误")
    
    # 按下回车 选择票类
    tab.actions.key_down('ENTER')

    # 按5次TAB切换到确定按钮
    for _ in range(5):
        tab.actions.key_down('TAB')

    # 按下确定按钮
    tab.actions.key_down('ENTER')

    # 等待表单页面加载完成
    tab.wait.load_start() 

    try:
        tab.ele("tag:span@@text()=我知道了").click()
    except:
        pass

    # 整个开票表单
    blue_invoice_ele=tab.ele('@class=blue-invoice')

    # 是否开票给自然人
    is_person_ele=blue_invoice_ele.ele("tag:span@@text()=是否开票给自然人")
    
    if is_person:
        is_person_ele.click()
        try:
            tab.ele("tag:span@@text()=我知道了").click()
        except:
            pass


    form_eles=blue_invoice_ele.eles('@class=t-col t-col-6')
    
    # 填写购买方信息
    input_eles=form_eles[0].eles('.t-input__inner')
    buy_content=(buy_name,buy_id,buy_address,buy_phone,buy_bank_name,buy_bank_id)
    for i in range(6):
        input_eles[i].input(buy_content[i])

    # 填写销售方信息
    input_eles=form_eles[1].eles('.t-input__inner')
    a=input_eles[4]
    
    # 如果销售方银行名称输入框为空，则输入销售方银行名称
    if input_eles[4].value == "" or input_eles[4].value == None:
        input_eles[4].input(sell_bank_name)

    # 如果销售方银行账号输入框为空，则输入销售方银行账号
    if input_eles[5].value == "" or input_eles[5].value == None:
        input_eles[5].input(sell_bank_id)


