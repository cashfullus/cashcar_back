import bcrypt

# Mysql 데이터베이스
from ..database.dbConnection import Database
# JwtToken
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

# 시간
import datetime


def datetime_to_str(time):
    return time.strftime('%Y-%m-%d %H:%M:%S')


# 회원가입
def register(**kwargs):
    # 데이터베이스 클래스 변수 저장 및 핸드폰 번호 중복 확
    db = Database()
    user = db.getUserByPhoneNumber(kwargs.get("phone_number"))
    if user:
        return False

    # 비밀번호 복호화 및 jwt 와 refresh 토큰 발행
    encrypted_password = bcrypt.hashpw(
        kwargs.get("password").encode("utf-8"),
        bcrypt.gensalt()).decode("utf-8")

    # kwargs 딕셔너리에 복호화된 password로 변경
    kwargs["password"] = encrypted_password

    # mysql insert 문
    sql = "INSERT INTO user (name, email, phone_number, password) VALUES " \
          "(%s, %s, %s, %s)"

    # Dictionary 형태 그대로 시도해보았으나 args부족이라는 에러만 발생하여 Dict를 보내도 for문을 한번 더 진행하니
    # 2중 반복문이 아니기때문에 속도적인 면에서 문제없어보임
    valueList = [val for key, val in kwargs.items()]
    db.execute(query=sql, args=valueList)
    db.commit()

    # Token 의 identity 를 user_id로 설정하기위해 한번의 select문 사용
    # 회원가입때 안할시 매 토큰 확인할때 select 문을 추가로 사용하여야 하여 회원가입할때 한번의 select 와 update를 사용
    query = "SELECT user_id FROM user WHERE phone_number = %s"
    # 방금가입한 회원의 user_id 조회
    target_user = db.executeOne(query=query, args=kwargs.get("phone_number"))
    # Jwt_Token 의 identity 를 user_id로 설정, 현재 무재한 토큰(Expired 설정 X)
    jwt_token = create_access_token(identity=target_user["user_id"], expires_delta=False)

    # 회원가입한 사용자의 토큰 update
    target_query = f"UPDATE user SET jwt_token = %s WHERE user_id = {target_user['user_id']}"
    db.execute(query=target_query, args=jwt_token)
    db.commit()
    return True


# 로그인

def login(**kwargs):
    db = Database()
    user = db.getUserByPhoneNumber(kwargs.get('phone_number'))
    if user:
        # 제한된 데이터만 response
        login_user = {}
        encode_password = kwargs.get('password').encode('utf8')
        if bcrypt.checkpw(encode_password, user["password"].encode('utf8')):
            login_user.setdefault("user_id", user["user_id"])
            login_user.setdefault("jwt_token", user["jwt_token"])
            return login_user
        else:
            return False
    else:
        return False




