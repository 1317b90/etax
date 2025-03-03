from typing import Optional
from pydantic import BaseModel

# 基础发票模型
class BaseInvoice(BaseModel):
    buy_name: str  # 购买方名称（发票抬头）
    buy_id: str = ""  # 购买方社会统一代码或身份证号码
    buy_email: str = ""  # 购买方邮箱号
    buy_address: str = ""  # 购买方地址
    buy_phone: str = ""  # 购买方电话
    buy_bank_name: str = ""  # 购买方开户银行名称
    buy_bank_id: str = ""  # 购买方开户银行卡号

    sell_bank_name:str=""
    sell_bank_id:str=""

    invoice_type: str  # 发票类型
    invoice_name: str  # 开票项目(商品名称)
    invoice_amount: str  # 金额
    invoice_model:str = ""  # 规格
    invoice_unit: str = ""  # 单位
    invoice_num: str = ""  # 数量
    invoice_price: str = ""  # 单价
    invoice_code: str = ""  # 项目编码(商品编码)
    is_preview: bool = True  # 是否预览发票

# 外壳
class Shell(BaseInvoice):
    class Config:
        extra = "ignore"  # 忽略额外的字段

    userid: str
    serviceid: str
    taskid: int  # 任务ID，支持字符串或数字
    company_name:str=""
    uscid:str  # 税号
    dsj_username: str  # 用户名
    dsj_password:str   # 密码
    adminid: Optional[str] = None  # 管理员ID，可选参数
    group_name: Optional[str] = None  # 组名，可选参数
# 执行时
class Execute(BaseInvoice):
    uscid:str  # 税号
    dsj_username:str  # 用户名
    dsj_password:str  # 密码