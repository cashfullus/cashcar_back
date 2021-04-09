import bcrypt

# Mysql 데이터베이스
from ..database.dbConnection import Database
# JwtToken
from flask_jwt_extended import create_access_token, create_refresh_token

# 시간
import datetime
import re


# 이메일 형태 정규식 사용하여 검사
def check_email_regex(email):
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    if re.search(regex, email):
        return True
    else:
        return False


# Datetime to String
def datetime_to_str(time):
    return time.strftime('%Y-%m-%d %H:%M:%S')


# 회원가입
def register(**kwargs):
    db = Database()
    result = {"status": True, "email_regex": True, "register_type": True, "data": ""}
    # Email 정규식 검사
    check_email = check_email_regex(kwargs.get("email"))
    # Email 중복확인
    user = db.getUserByEmail(kwargs.get("email"))
    # 확인사항 검사
    if check_email is False:
        result["email_regex"] = False
        return result

    elif user:
        result["status"] = False
        return result

    # 기본 회원가입 Query
    sql = "INSERT INTO user(email, hashed_password, login_type) VALUES (%s, %s, %s)"

    # 카카오 회원일 경우 Query
    if kwargs.get("login_type") == "kakao":
        sql = "INSERT INTO user(email, login_type) VALUES (%s, %s)"

    # 앱 기본 회원가입일 경우 password 복호화
    elif kwargs.get("login_type") == "normal":
        if kwargs.get("password") is None:
            result["status"] = False
            return result

        encrypted_password = bcrypt.hashpw(
            kwargs.get("password").encode("utf-8"),
            bcrypt.gensalt()).decode("utf-8")
        kwargs["password"] = encrypted_password
    # 정해지지않은 회원가입 시도
    else:
        result["register_type"] = False
        return result

    value_list = [val for key, val in kwargs.items()]
    db.execute(query=sql, args=value_list)
    db.commit()

    # JwtToken 을 업데이트 하기위해 User 정보 가져오기
    target_user = db.executeOne(query="SELECT user_id FROM user WHERE email = %s", args=kwargs.get("email"))
    # JwtToken
    jwt_token = create_access_token(identity=target_user["user_id"], expires_delta=False)
    update_user = f"UPDATE user SET jwt_token = %s WHERE user_id = {target_user['user_id']}"
    db.execute(query=update_user, args=jwt_token)
    db.commit()

    result["data"] = {"user_id": target_user["user_id"], "jwt_token": jwt_token}
    return result


# 로그인
def login(**kwargs):
    db = Database()
    user = db.getAllLoginTypeUserByEmail(email=kwargs.get("email"), login_type=kwargs.get("login_type"))
    if user:
        # 제한된 데이터만 response
        if kwargs.get("login_type") == "kakao":
            login_user = {"user_id", user["user_id"], "jwt_token", user["jwt_token"]}
            return login_user

        elif kwargs.get("login_type") == "normal":

            encode_password = kwargs.get('password').encode('utf8')
            if bcrypt.checkpw(encode_password, user["password"].encode('utf8')):
                login_user = {"user_id", user["user_id"], "jwt_token", user["jwt_token"]}
                return login_user
            else:
                return False
        else:
            return False
    else:
        return False


# Fcm 토큰 저장
def user_fcm(**kwargs):
    db = Database()
    user = db.getUserById(user_id=kwargs.get("user_id"))
    if user:
        fcm_row = db.executeOne(query="SELECT * FROM user_fcm WHERE user_id = %s", args=kwargs.get("user_id"))
        if fcm_row:
            db.execute(query="UPDATE user_fcm SET fcm_token = %s, "
                             "last_check_time = NOW() WHERE fcm_id = %s",
                       args=[fcm_row["fcm_token"], fcm_row["fcm_id"]]
                       )
            db.commit()
            return True
        else:
            db.execute(query="INSERT INTO user_fcm (user_id, fcm_token) VALUES (%s, %s)",
                       args=[kwargs.get("user_id"), kwargs.get("fcm_token")]
                       )
            db.commit()
            return True
    else:
        return False
