import make_invoice

if __name__ == "__main__":
    # 是否预览
    is_preview=True
    make_invoice.main(
        uscid = "92440101MA5ACL5772",   
        dsj_username = "18620128421",
        dsj_password = "tj190802",
        # uscid = "91440104MABM9B4CXD",   
        # dsj_username = "Zhjj111",
        # dsj_password = "Aa123456",

        # uscid="91440111MADJE53231",
        # dsj_username="441423199111124015",
        # dsj_password="shuiwu12345",

        invoice_type="普通发票",
        # invoice_type="增值税专用发票"

        # 购买方信息
        buy_name="广州渠道网络技术有限公司;",
        buy_id="91440101MA9Y2LUM33",
        buy_address="广州市白云区云城东路513号503",
        buy_phone="18588619551",
        buy_bank_name="招商银行股份有限公司广州机场路支行",
        buy_bank_id="120920070910601",

        # 销售方信息
        sell_bank_name="中国农业银行广州环市支行",
        sell_bank_id="6230520080008343378",

        # 发票信息
        #项目名称
        invoice_name="餐费",
        # 规格型号
        invoice_model="",
        # 单位
        invoice_unit="",
        # 数量
        invoice_num="8",
        # 单价
        invoice_price="",
        # 金额
        invoice_amount="62.64",

        is_preview=True,
        invoice_code="",

        wecome_id=None, # 企业微信ID
        task_id=None, # 任务ID
        buy_email=None, # 购买方邮箱
        company_name=None, # 销售方公司名称
    )

