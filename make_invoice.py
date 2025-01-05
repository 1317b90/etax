# 导入
import random
import time
from DrissionPage import Chromium, ChromiumOptions, SessionPage
import ddddocr
from DrissionPage.common import Settings

import Config

#设置找不到元素时，抛出异常
Settings.raise_when_ele_not_found = True
#设置点击失败时，抛出异常
Settings.raise_when_click_failed = True
#设置等待失败时，抛出异常
Settings.raise_when_wait_failed = True
#设置单例化标签页对象
Settings.singleton_tab_obj = True


def main(
    uscid,  # 税号
    dsj_username,  # 用户名
    dsj_password,  # 密码
    buy_name,  # 购买方名称
    invoice_name,  # 项目名称
    invoice_amount,  # 金额
    invoice_type="普通发票",  # 发票类型

    
    buy_id="",  # 购买方ID
    buy_address="",  # 购买方地址
    buy_phone="",  # 购买方电话
    buy_bank_name="",  # 购买方银行名称
    buy_bank_id="",  # 购买方银行账号
    sell_bank_name="",  # 销售方银行名称
    sell_bank_id="",  # 销售方银行账号
    
    invoice_model="",  # 规格型号
    invoice_unit="",  # 单位
    invoice_num="",  # 数量
    invoice_price="",  # 单价
 
    invoice_code="",  # 项目编码
    is_preview=True,  # 是否预览
    
    # 装饰参数
    wecome_id=None, # 企业微信ID
    task_id=None, # 任务ID
    buy_email=None, # 购买方邮箱
    company_name=None, # 销售方公司名称
):

    # ——————————加载页面————————————————————加载页面————————————————————加载页面————————————————————加载页面————————————————————加载页面——————————
    co = ChromiumOptions()
    co.set_timeouts(base=Config.TIMEOUTS)



    # 连接浏览器
    browser = Chromium()  
    try:
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
        det = ddddocr.DdddOcr(det=False, ocr=False,show_ad=False)

        MAX_LOGIN_ATTEMPTS = 6
        
        for attempt in range(MAX_LOGIN_ATTEMPTS):
            # 第一次登录不刷新页面，后续登录需要刷新
            is_refresh = attempt > 0
            
            if login(det, tab, uscid, dsj_username, dsj_password, is_refresh):
                break
        else:
            raise Exception("多次登录失败")
        
        # 登录成功了，点击办税员
        tab.ele("@@class=el-radio__label@@text()=办税员").click()

        # 接着点击确定
        tab.ele('tag:span@@text()=确认').click()

        tab.wait.load_start() 

        # 访问立即开票页面
        tab.get('https://dppt.guangdong.chinatax.gov.cn:8443/blue-invoice-makeout')

        tab.wait.load_start() 

        Config.wait()

        # 点击立即开票
        tab.wait.eles_loaded('tag:div@@text()=立即开票')
        time.sleep(1)
        tab.ele('tag:div@@text()=立即开票').click()
        
        # 是否个人
        is_person=False  # 是否个人

        # 假如名字小于4个字，则认为是个人
        if len(buy_name)<=4:
            is_person=True

        # 等待票类选择框出现
        Config.wait()
        tab.wait.eles_loaded('tag:label@@text()=选择票类')
        

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
        Config.wait()

        # 整个开票表单
        blue_invoice_ele=tab.ele('@class=blue-invoice')

        # 是否开票给自然人
        if is_person:
            tab.ele("@@class=t-checkbox__label@@text()=是否开票给自然人").click(by_js=True)

        # 此时有可能有遮罩框框
        Config.wait()
        
        # 提示框
        try:
            iknows=tab.eles("tag:span@@text()=我知道了")
            for iknow in iknows:
                iknow.click(by_js=None)
        except:
            print("不 你不知道")

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


        # 填写发票信息
        t_table_ele=tab.ele('@class=t-table__body')

        invoice_tr_ele=t_table_ele.ele('@tag()=tr')
        # 开票信息输入框
        input_eles=invoice_tr_ele.eles('@tag()=input')


        # 如果不是自带编码
        if invoice_code == "":
            # 点击填写项目名称按钮
            invoice_tr_ele.ele('@tag()=button',timeout=10).click()

            Config.wait()

            # 右侧扩展界面
            right_ele=tab.ele('@class=tree-layout-container__content-main')

            tab.wait.eles_loaded('@class=search-control-panel t-form')

            # 表单
            form_ele=right_ele.ele('@class=search-control-panel t-form')

            # 填写项目名称
            form_ele.ele('@class=t-input__inner').input(invoice_name)

            # 搜索
            form_ele.ele('tag:span@@text()=查询').click()

            # 等待表单页面加载完成
            Config.wait()

            # 搜索结果表格
            table_ele=right_ele.ele('@class=t-table__body')

            # 默认选择第一行
            tr_ele=table_ele.ele('@tag()=tr')

            # 看看有多少列
            td_eles=tr_ele.eles('@tag()=td')

            # 如果搜索结果为空
            if len(td_eles) <= 1:
                raise Exception("需查询编码")
            
            # 如果搜索结果存在，点击最后的选择按钮
            td_eles[-1].ele("tag:span@@text()=选择").click(by_js=True)
        
        # 如果自带编码
        else:
            # 单击项目名称输入框，弹出“自行选择商品编码”
            input_eles[1].click()

            Config.wait()

            # 等待并点击自行选择商品编码
            tab.wait.eles_loaded('@class=auto-complete__handle')
            tab.ele("@class=auto-complete__handle").click()

            Config.wait()

            # 等待左侧容器加载完成
            tab.wait.eles_loaded('@class=left-container')
            left_container_ele=tab.ele("@class=left-container")
            left_input_eles=left_container_ele.eles('@tag()=input')

            left_input_eles[1].input(invoice_name)
            left_input_eles[2].input(invoice_code)

            # 等待并点击匹配的编码
            tab.wait.eles_loaded('@class=auto-complete__item')
            tab.ele('@class=auto-complete__item').click()

            # 找到税率
            left_input_eles[2].click()
            for _ in range(6):
                tab.actions.key_down('TAB')

            tab.actions.key_down('DOWN')
            tab.actions.key_down('ENTER')

            # 点击确定
            tab.ele("@@class=t-button__text@@text()=保存并带入当前行").click()

            
            # 自带编码确认后，需要重新获取一遍发票信息组件

            t_table_ele=tab.ele('@class=t-table__body')
            invoice_tr_ele=t_table_ele.ele('@tag()=tr')
            input_eles=invoice_tr_ele.eles('@tag()=input')

        Config.wait()
        
        # 依次填写规格型号、单位、数量、单价、金额
        invoice_values=(invoice_model,invoice_unit,invoice_num,invoice_price,invoice_amount)
        for i in range(5):
            if invoice_values[i] != "":
                time.sleep(Config.TIMEWAIT/2)
                input_eles[i+2].input(invoice_values[i])

        Config.wait()

        # 最底部的按钮
        footer_ele=tab.ele('@class=hide-side-layout__container-footer')

        # 获取按钮
        footer_buttons=footer_ele.eles('@tag()=button')


        # 如果需要预览
        if is_preview:
            # 点击预览发票
            footer_buttons[1].click()
            Config.wait()
            # 等待预览发票页面加载完成
            tab.wait.eles_loaded('tag:div@@text()=发票预览')
            tab.get_screenshot(path='./files', name='preview.jpg', full_page=True)

            raise Exception("发票预览")
        
        else:
            # 不需要预览，直接开具发票
            footer_buttons[2].click()
            Config.wait()
            try:
                down_ele=tab.ele('@@class=t-button__text@@text()=发票下载PDF')
                down_ele.wait.has_rect()
            
                mission = down_ele.click.to_download(save_path='./files', rename="invoice.pdf")
                mission.wait()
            except:
                raise Exception("开票成功，但下载发票文件失败")
 
            raise Exception("开票完成")
    except Exception as e:
        raise Exception(e)
    finally:
        
        browser.quit() 

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

        raise Exception("登录失败："+message_ele.text)
    except:
        pass


    # 不报错，说明按钮存在，则没通过验证
    try:
        dialog_ele.ele('@class=slide-verify-slider-mask-item-icon',timeout=1)
        return False
    except:
        return True

# ——————————登录————————————————————登录————————————————————登录————————————————————登录————————————————————登录————————————————————登录——————————
def login(det,tab,uscid,dsj_username,dsj_password,is_refresh=False):
    
        
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

        input_content = (uscid,dsj_username,dsj_password)

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
        if "登录失败：" in str(e):
            raise Exception(str(e))
        # 如果是其他的错误，重试就可以了
        else:
            print("登录失败：",str(e))
            return False
