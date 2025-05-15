import models
import make_invoice


data=models.Execute(
    invoice_type="普通发票",
    invoice_name="餐费",
    invoice_amount="100.18",
    #invoice_code="1060510090000000000",
    buy_name="测试",
    buy_email="1317b90@gmail.com",
    company_name="测试",
    is_preview=True,
    serviceid="admin",
    userid="admin_flx",
    adminid="admin",
    group_name="test",
    taskid="test",
    uscid="92440101MA5ACL5772",
    dsj_username="18620128421",
    dsj_password="tj190802",
    sell_bank_id="1000000000000000000",
    sell_bank_name="测试",
)

make_invoice.main(data)
