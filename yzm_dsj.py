import requests
import json
import ddddocr
import base64

def main():
    try:
        data=args.get("response_body_list",[0])
        response_body = json.loads(data[0]["body"])
        if response_body["msg"] == "处理成功！":
            imgDatas = json.loads(response_body['datagram'])
        else:
            raise Exception("监听数据有误")

        canvasImg64 = imgDatas["canvasSrc"]
        blockImg64 = imgDatas["blockSrc"]
        canvas_data = canvasImg64.split(',')[1]  # Remove the data:image/jpg;base64 prefix
        canvas_bytes = base64.b64decode(canvas_data)
        block_data = blockImg64.split(',')[1]  # Remove the data:image/png;base64 prefix
        block_bytes = base64.b64decode(block_data)
        det = ddddocr.DdddOcr(det=False, ocr=False)

        res = det.slide_match(block_bytes,canvas_bytes)

        # 返回偏移的x坐标
        args["res"] = res['target'][0]
    except Exception as e:
    #     print(str(e))
        args["res"] = 0 
    finally:
        del args["response_body_list"]