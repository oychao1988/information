from flask import current_app
from qiniu import Auth, put_data

access_key = "W0oGRaBkAhrcppAbz6Nc8-q5EcXfL5vLRashY4SI"
secret_key = "tsYCBckepW4CqW0uHb9RdfDMXRDOTEpYecJAMItL"

def qiniu_image_store(data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    bucket_name = 'python-ihome'
    token = q.upload_token(bucket_name)
    try:
        ret, info = put_data(token, None, data)
        if ret and info.status_code == 200:
            return ret['key']
    except Exception as e:
        current_app.logger.error(e)
        raise e