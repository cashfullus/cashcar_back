import bcrypt

# Mysql 데이터베이스
from ..database.dbConnection import Database
# JwtToken
from flask_jwt_extended import create_access_token

# 시간
import datetime
import re
import os


def allowed_in_role_user(user_id):
    db = Database()
    user_role = db.executeOne(
        query="SELECT role FROM admin_user WHERE admin_user_id = %s AND role IN ('staff', 'superuser')",
        args=user_id
    )
    if user_role:
        return True
    else:
        return False


def register(**kwargs):
    db = Database()
    result = {"exist_id": True, "data": {}}
    exist_user = db.executeOne(
        query="SELECT admin_user_id FROM admin_user WHERE login_id = %s",
        args=kwargs['login_id']
    )
    if exist_user:
        result["exist_id"] = False
        return result

    sql = "INSERT INTO admin_user (login_id, hashed_password) VALUES (%s, %s)"
    encrypted_password = bcrypt.hashpw(kwargs.get("password").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    value_list = [kwargs['login_id'], encrypted_password]
    db.execute(query=sql, args=value_list)
    db.commit()

    # JwtToken 을 업데이트 하기위해 User 정보 가져오기
    target_user = db.executeOne(query="SELECT admin_user_id FROM admin_user WHERE login_id = %s",
                                args=kwargs['login_id'])
    # JwtToken
    jwt_token = create_access_token(identity=target_user["admin_user_id"], expires_delta=False)
    update_user = "UPDATE admin_user SET jwt_token = %s WHERE admin_user_id = %s"
    db.execute(query=update_user, args=[jwt_token, target_user["admin_user_id"]])
    db.commit()
    result["data"] = db.executeOne(
        query="SELECT admin_user_id, jwt_token, role FROM admin_user WHERE login_id = %s",
        args=kwargs['login_id']
    )
    return result


# 로그인
def login(**kwargs):
    db = Database()
    status = {"login_id": True, "password": True, "data": {}}
    admin_user = db.executeOne(
        query="SELECT admin_user_id, hashed_password, jwt_token, role FROM admin_user WHERE login_id = %s",
        args=kwargs['login_id']
    )
    if not admin_user:
        status["login_id"] = False
        return status

    encode_password = kwargs['password'].encode('utf8')
    if bcrypt.checkpw(encode_password, admin_user['hashed_password'].encode('utf8')):
        status["data"] = {"user_id": admin_user["admin_user_id"], "jwt_token": admin_user["jwt_token"]}
        return status
    else:
        status["password"] = False
        return status

