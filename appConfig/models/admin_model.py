import bcrypt

# Mysql 데이터베이스
from database.dbConnection import Database
# JwtToken
from flask_jwt_extended import create_access_token

# 시간
from datetime import datetime, date, timedelta
import os
from notification.user_push_nofitication import one_cloud_messaging


def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


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


# 사용자 공지사항 리스트
def user_get_notice_list():
    db = Database()
    result = db.getUserAllNotice()
    return result


# 어드민 공지사항 등록
def admin_register_notice(**kwargs):
    db = Database()
    db.execute(
        query="INSERT INTO notice_information (title, description) VALUES (%s, %s)",
        args=[kwargs['title'], kwargs['description']]
    )
    result = db.executeOne(
        query="SELECT notice_id, title, description, "
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM notice_information ORDER BY register_time DESC LIMIT 1"
    )
    db.commit()
    return result


# 어드민 공지사항 리스트
def admin_get_notice_list(page, count):
    per_page = (int(page) - 1) * int(count)
    db = Database()
    result = db.getAdminAllNotice(count=int(count), per_page=per_page)
    item_count = db.executeOne(
        query="SELECT count(notice_id) as item_count "
              "FROM notice_information WHERE is_removed = 0",
    )
    return result, item_count['item_count']


# 공지사항 업데이트
def update_notice(notice_id, **kwargs):
    db = Database()
    db.updateNotice(notice_id=notice_id, title=kwargs.get('title'), description=kwargs.get('description'))
    kwargs['notice_id'] = int(notice_id)
    return kwargs


# 공지사항 삭제 (실제 데이터는 삭제되지 않는다.)
def delete_notice(notice_id):
    db = Database()
    db.deleteNotice(notice_id=notice_id)
    return True


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


# 어드민 광고 리스트 (query string)
def get_all_by_admin_ad_list(category, avg_point, area, gender, avg_age, distance, recruit_start, recruit_end, order_by,
                             sort, page, count):
    db = Database()
    per_page = (page - 1) * int(count)
    status = {"correct_category": True}
    category_value = ""
    if category == "ongoing":
        category_value = "recruit_start_date <= NOW() AND recruit_end_date >= NOW()"
    elif category == "scheduled":
        category_value = "recruit_start_date > NOW()"
    elif category == "done":
        category_value = "recruit_end_date < NOW() OR max_recruiting_count = recruiting_count"
    elif category == 'none':
        category_value = "((recruit_start_date <= NOW() AND recruit_end_date >= NOW()) " \
                         "OR (recruit_start_date > NOW()) " \
                         "OR (recruit_end_date < NOW() OR max_recruiting_count = recruiting_count)) "
    else:
        status["correct_category"] = False

    # 포인트가 최솟값보다 크고 최대값보다 작은 데이터
    where_point = f"(total_point >= {avg_point[0]} AND total_point <= {avg_point[1]})"
    where_area = []
    if type(area) == str:
        if area == "":
            where_area = "area LIKE '%%'"
        else:
            where_area = f"area LIKE '%%{area}%%'"
    else:
        for i in range(len(area)):
            if i + 1 != len(area):
                where_area.append(f"area LIKE '%%{area[i]}%%' OR ")
            else:
                where_area.append(f"area LIKE '%%{area[i]}%%'")
        where_area = "({0})".format(''.join(where_area))
    if int(gender) == 0:
        where_gender = f"gender IN (0, 1, 2)"
    else:
        where_gender = f"gender IN ({gender})"
    where_distance = f"min_distance >= {distance}"
    where_age = f"(min_age_group >= {avg_age[0]} AND max_age_group <= {avg_age[1]})"
    where_recruit_date = f"(recruit_start_date >= '{recruit_start} 00:00:00' AND recruit_end_date <= '{recruit_end} 00:00:00')"

    sql = "SELECT ad_id, owner_name, title, thumbnail_image, activity_period, ad_status, " \
          "max_recruiting_count, recruiting_count, total_point, " \
          "day_point, area, description, gender, min_distance, min_age_group, " \
          "max_age_group, side_image, back_image, side_length, side_width, " \
          "back_length, back_width, " \
          "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
          "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date " \
          "FROM ad_information " \
          f"WHERE {category_value} AND {where_point} " \
          f"AND {where_area} AND {where_gender} " \
          f"AND {where_distance} AND {where_age} AND {where_recruit_date} ORDER BY {order_by} {sort} LIMIT %s OFFSET %s"
    result = db.executeAll(query=sql, args=[int(count), per_page])
    item_count = db.executeOne(
        query="SELECT count(ad_id) as item_count FROM ad_information "
              f"WHERE {category_value} AND {where_point} "
              f"AND {where_area} AND {where_gender} "
              f"AND {where_distance} AND {where_age} AND {where_recruit_date}"
    )
    if result:
        for i in range(len(result)):
            result[i]['ad_images'] = db.executeAll(
                query='SELECT image FROM ad_images WHERE ad_id = %s',
                args=result[i]['ad_id']
            )
            result[i]['default_mission_items'] = db.executeAll(
                query='SELECT '
                      'mission_type, due_date, `order`, based_on_activity_period '
                      'FROM ad_mission_card WHERE ad_id = %s AND mission_type = 0',
                args=result[i]['ad_id']
            )
            result[i]['additional_mission_items'] = db.executeAll(
                query='SELECT '
                      'mission_type, due_date, `order`, based_on_activity_period, '
                      'from_default_order_date, from_default_order, mission_name, additional_point '
                      'FROM ad_mission_card WHERE ad_id = %s AND mission_type = 1',
                args=result[i]['ad_id']
            )
    return result, item_count['item_count']


# # 어드민이 미션 성공여부 체크
def admin_accept_mission(ad_apply_id, mission_card_id, **kwargs):
    db = Database()
    status = kwargs['status']
    result = {"accept": True, "reason": "Update Success"}
    mission_information = db.getOneMissionUserInfoByIdx(ad_user_apply_id=ad_apply_id,
                                                        ad_mission_card_id=mission_card_id)
    if mission_information:
        # 이미 바껴있는 값으로 바꿀경우 fail = fail, success = success, reject = reject
        if status == mission_information['status']:
            result["reason"] = "Already Change Status"
            result["accept"] = False
            return result

        elif (status == "fail" or status == "reject") and mission_information['status'] == "success":
            result["reason"] = "Already Success Mission"
            result["accept"] = False
            return result

        else:
            pass

        # 미션 성공일 경우
        if status == 'success':
            # 미션 타입에 따라(필수, 선택) 성공 횟수 추가
            if mission_information['mission_type'] == 0:
                db.execute(
                    query="UPDATE ad_user_apply "
                          "SET default_mission_success_count = default_mission_success_count + 1 "
                          "WHERE ad_user_apply_id = %s",
                    args=ad_apply_id
                )
            else:
                db.execute(
                    query="UPDATE ad_user_apply "
                          "SET additional_mission_success_count = additional_mission_success_count + 1 "
                          "WHERE ad_user_apply_id = %s",
                    args=ad_apply_id
                )
            # 미션 성공으로 업데이트
            db.execute(
                query="UPDATE ad_mission_card_user "
                      "SET status = 'success', mission_success_datetime = NOW() WHERE ad_mission_card_user_id = %s",
                args=mission_information['ad_mission_card_user_id']
            )
            # 필수미션 회차에 따른 추가 미션 정보 조회
            additional_mission_list = db.getAllAddMissionUserInfoByApplyIdFirst(
                ad_user_apply_id=ad_apply_id,
                ad_mission_card_id=mission_card_id,
                from_default_order=mission_information['order']
            )
            if additional_mission_list:
                for mission in additional_mission_list:
                    start_date = date.today() + timedelta(days=(int(mission['from_default_order_date'])))
                    end_date = start_date + timedelta(days=(int(mission['due_date']) - 1))
                    db.execute(
                        query="UPDATE ad_mission_card_user "
                              "SET mission_start_date = %s, mission_end_date = %s "
                              "WHERE ad_mission_card_user_id = %s",
                        args=[start_date.strftime('%Y-%m-%d 00:00:00'),
                              end_date.strftime('%Y-%m-%d 23:59:59'),
                              mission['ad_mission_card_user_id']
                              ]
                    )
            if mission_information['order'] == 1 and mission_information['mission_type'] == 0:
                start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                end_date = (date.today() + timedelta(days=(int(mission_information['activity_period']) - 1))) \
                    .strftime('%Y-%m-%d 23:59:59')
                db.execute(
                    query="UPDATE ad_user_apply "
                          "SET activity_start_date = %s, activity_end_date = %s WHERE ad_user_apply_id = %s",
                    args=[start_date, end_date, ad_apply_id]
                )
            history_name = f"{mission_information['title']} 광고 {mission_information['mission_name']} 승인"
            body_name = f"[{mission_information['mission_name']}]에 성공하였습니다. 축하드립니다 :)"
            db.execute(
                query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                args=[mission_information['user_id'], history_name]
            )
            one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
            db.execute(
                query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                      "VALUES (%s, %s, %s, %s)",
                args=[mission_information['user_id'], "mission", 1, body_name]
            )
            save_message_name = f"{mission_information['mission_name']} 성공"
            db.saveStatusMessage(
                ad_user_apply_id=ad_apply_id, reason=save_message_name, message_type="mission_success"
            )
            db.commit()
            return result

        elif status == 'reject':
            # 이미 한번 실패했을 경우
            if mission_information['mission_fail_count'] == 1:
                # 필수미션이 한번 이미 실패했을 경우 광고집행 실패
                if mission_information['mission_type'] == 0:
                    title = "신청한 서포터즈 활동에 실패했습니다:("
                    reason = """서포터즈 활동 미션 인증에 실패하였습니다. 활동 미행으로 리워드는 지급해드리지 않으며 다른 서포터즈 활동에 지원해주세요."""
                    db.execute(
                        query="UPDATE ad_mission_card_user "
                              "SET status = 'fail', mission_fail_count = mission_fail_count + 1 "
                              "WHERE ad_user_apply_id = %s",
                        args=ad_apply_id
                    )
                    db.execute(
                        query="UPDATE ad_user_apply SET status = 'fail' WHERE ad_user_apply_id = %s",
                        args=ad_apply_id
                    )
                    db.saveStatusMessage(
                        ad_user_apply_id=ad_apply_id, title=title, reason=reason, message_type="apply_fail"
                    )
                    body_name = f"[{mission_information['mission_name']}] 인증에 실패하였습니다. 다음 기회에 다시 도전해주세요 :("
                    db.execute(
                        query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                              "VALUES (%s, %s, %s, %s)",
                        args=[mission_information['user_id'], "mission", 1, body_name]
                    )
                    one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
                    db.commit()
                    return result
                # 추가 미션의 경우 실패해도 상관없음(point 미지급)
                else:
                    title = "미션 인증에 실패하였습니다:("
                    reason = "또 다른 미션을 통해 리워드를 지급받으세요!"
                    db.execute(
                        query="UPDATE ad_mission_card_user "
                              "SET status = 'fail', mission_fail_count =  mission_fail_count + 1 "
                              "WHERE ad_mission_card_id = %s",
                        args=mission_card_id
                    )
                    db.saveStatusMessage(
                        ad_user_apply_id=ad_apply_id, title=title, reason=reason, message_type="mission_fail"
                    )
                history_name = f"{mission_information['title']} 광고 {mission_information['mission_name']} 실패"
                db.execute(
                    query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                    args=[mission_information['user_id'], history_name]
                )
                body_name = f"[{mission_information['mission_name']}] 인증에 실패하였습니다. 다음 기회에 다시 도전해주세요ㅠㅜ"
                db.execute(
                    query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                          "VALUES (%s, %s, %s, %s)",
                    args=[mission_information['user_id'], "mission", 1, body_name]
                )
                one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
                db.commit()
                return result

            else:
                body_name = f"[{mission_information['mission_name']}]의 재인증에 도전해주세요!"
                title = "미션 인증에 실패하였습니다:("
                reason = f"""{kwargs['reason']} 재인증에도 실패할 경우, 리워드가 지급되지 않으니 기한 내 재인증 부탁드립니다!"""
                history_name = f"{mission_information['title']} 광고 {mission_information['mission_name']} 실패"
                db.execute(
                    query="UPDATE ad_mission_card_user "
                          "SET status = 'reject', mission_fail_count = mission_fail_count + 1 "
                          "WHERE ad_mission_card_id = %s",
                    args=mission_card_id
                )
                db.execute(
                    query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                    args=[mission_information['user_id'], history_name]
                )
                db.saveStatusMessage(
                    ad_user_apply_id=ad_apply_id, title=title, reason=reason, message_type="mission_fail"
                )
                db.execute(
                    query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                          "VALUES (%s, %s, %s, %s)",
                    args=[mission_information['user_id'], "mission", 1, body_name]
                )
                one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
                db.commit()
                return result


# 어드민 회원리스트 및 회원 관리  모집번호 추가
def get_all_user_list(page, count):
    db = Database()
    per_page = (int(page) - 1) * int(count)
    user_list = db.executeAll(
        query="SELECT user_id, nickname, name, call_number, email, "
              "resident_registration_number_back as gender, "
              "resident_registration_number_front as date_of_birth, "
              "marketing, main_address, detail_address, deposit, "
              "DATE_FORMAT(u.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM user u LIMIT %s OFFSET %s",
        args=[int(count), per_page]
    )
    item_count = db.executeOne(
        query="SELECT count(user_id) as item_count FROM user"
    )
    if user_list:
        for i in range(len(user_list)):
            vehicle = db.executeAll(
                query="SELECT "
                      "vehicle_id, vehicle_model_name, car_number, brand,owner_relationship, supporters "
                      "FROM vehicle WHERE user_id = %s AND removed = 0",
                args=user_list[i]['user_id']
            )
            activity_history = db.executeAll(
                query="SELECT history_name, "
                      "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                      "FROM user_activity_history WHERE user_id = %s ORDER BY register_time DESC",
                args=user_list[i]['user_id']
            )
            user_list[i]['vehicle_information'] = vehicle
            user_list[i]['activity_history'] = activity_history

    return user_list, item_count['item_count']


# 어드민 회원 정보 수정
def admin_user_profile_modify(**kwargs):
    db = Database()
    db.execute(
        query="UPDATE user SET nickname = %s, email = %s, main_address = %s, detail_address = %s WHERE user_id = %s",
        args=[kwargs.get('nickname'), kwargs.get('email'), kwargs.get('main_address'),
              kwargs.get('detail_address'), kwargs.get('user_id')]
    )
    db.commit()
    return kwargs


# 어드민 포인트 출금 신청 리스트
def get_all_withdrawal_point(page, count):
    db = Database()
    per_page = (int(page) - 1) * int(count)
    result = db.executeAll(
        query="SELECT "
              "withdrawal_self_id, w.account_bank, name, w.account_number, user.user_id, amount, `status`, "
              "DATE_FORMAT(w.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, "
              "CASE WHEN w.change_done = '0000-00-00 00:00:00' THEN '' "
              "WHEN w.change_done IS NOT NULL "
              "THEN DATE_FORMAT(w.change_done, '%%Y-%%m-%%d %%H:%%i:%%s') END as change_done "
              "FROM user JOIN withdrawal_self w on user.user_id = w.user_id "
              "ORDER BY FIELD(`status`, 'waiting', 'checking', 'reject', 'cancel', 'done') LIMIT %s OFFSET %s",
        args=[int(count), per_page]
    )
    item_count = db.executeOne(
        query="SELECT count(withdrawal_self_id) as item_count FROM withdrawal_self"
    )
    return result, item_count['item_count']


# 어드민 포인트 출금 상태 변경  (waiting(대기중), confirm(확인), done(승인), reject(반려))
def update_withdrawal_point(**kwargs):
    result = withdrawal_total_result(withdrawal_type="point", **kwargs)
    return result


# 어드민 기부 신청 리스트
def get_all_withdrawal_donate(page, count):
    db = Database()
    per_page = (int(page) - 1) * int(count)
    result = db.executeAll(
        query="SELECT "
              "name, user.user_id, amount, `status`, wd.donation_organization, receipt, name_of_donor,"
              "DATE_FORMAT(wd.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, "
              "CASE WHEN wd.change_done = '0000-00-00 00:00:00' THEN '' "
              "WHEN wd.change_done IS NOT NULL "
              "THEN DATE_FORMAT(wd.change_done, '%%Y-%%m-%%d %%H:%%i:%%s') END as change_done, withdrawal_donate_id "
              "FROM user JOIN withdrawal_donate wd on user.user_id = wd.user_id "
              "ORDER BY FIELD(`status`, 'waiting', 'checking', 'reject', 'cancel', 'done') "
              "LIMIT %s OFFSET %s",
        args=[int(count), per_page]
    )
    item_count = db.executeOne(
        query="SELECT count(withdrawal_donate_id) as item_count FROM withdrawal_donate"
    )
    return result, item_count['item_count']


# 어드민 기부 출금 상태 변경 (waiting(대기중), checking(확인중), done(승인), reject(반려))
def update_withdrawal_donate(**kwargs):
    result = withdrawal_total_result(withdrawal_type="donate", **kwargs)
    return result


def withdrawal_total_result(withdrawal_type, **kwargs):
    db = Database()
    status_list = []
    if withdrawal_type == "point":
        user_list = kwargs['withdrawal_list']
        if user_list:
            if kwargs['status'] == "done":
                for i in range(len(user_list)):
                    user_information = db.executeOne(
                        query="SELECT u.user_id, deposit, amount FROM withdrawal_self "
                              "JOIN user u on withdrawal_self.user_id = u.user_id WHERE withdrawal_self_id = %s",
                        args=user_list[i]
                    )
                    if int(user_information['deposit']) - int(user_information["amount"]) >= 0:
                        db.execute(
                            query="UPDATE withdrawal_self "
                                  "SET status = 'done', change_done = NOW() "
                                  "WHERE withdrawal_self_id = %s",
                            args=user_list[i]
                        )
                        db.execute(
                            query="UPDATE user SET deposit = deposit - %s WHERE user_id = %s",
                            args=[int(user_information['amount']), user_information['user_id']]
                        )
                    else:
                        status_list.append({i: False})
                db.commit()
                return True
            elif kwargs['status'] == "reject":
                for i in range(len(user_list)):
                    db.execute(
                        query="UPDATE withdrawal_self "
                              "SET status = 'reject', change_reject = NOW() "
                              "WHERE withdrawal_self_id = %s",
                        args=user_list[i]
                    )
                db.commit()
                return True
            elif kwargs['status'] == "confirm":
                for i in range(len(user_list)):
                    db.execute(
                        query="UPDATE withdrawal_self "
                              "SET status = %s, change_confirm = NOW() "
                              "WHERE withdrawal_self_id = %s",
                        args=[kwargs['status'], user_list[i]]
                    )
                db.commit()
                return True
            else:
                return False
        else:
            return False

    elif withdrawal_type == "donate":
        user_list = kwargs['withdrawal_donate_list']
        if user_list:
            # 기부 완료
            if kwargs['status'] == "done":
                for i in range(len(user_list)):
                    user_information = db.executeOne(
                        query="SELECT u.user_id, deposit, amount FROM withdrawal_donate "
                              "JOIN user u on withdrawal_donate.user_id = u.user_id WHERE withdrawal_donate_id = %s",
                        args=user_list[i]
                    )
                    if int(user_information['deposit']) - int(user_information["amount"]) >= 0:
                        db.execute(
                            query="UPDATE withdrawal_donate SET status = 'done', change_done = NOW() "
                                  "WHERE withdrawal_donate_id = %s",
                            args=user_list[i]
                        )
                        db.execute(
                            query="UPDATE user SET deposit = deposit - %s WHERE user_id = %s",
                            args=[int(user_information['amount']), user_information['user_id']]
                        )
                    else:
                        status_list.append({i: False})
                db.commit()
                return True
            # 기부 reject
            elif kwargs['status'] == "reject":
                for i in range(len(user_list)):
                    db.execute(
                        query="UPDATE withdrawal_donate "
                              "SET status = 'reject', change_reject = NOW() "
                              "WHERE withdrawal_donate_id = %s",
                        args=user_list[i]
                    )
                db.commit()
                return True
            # 기부 진행중
            elif kwargs['status'] == "confirm":
                for i in range(len(user_list)):
                    db.execute(
                        query="UPDATE withdrawal_donate "
                              "SET status = %s, change_confirm = NOW() "
                              "WHERE withdrawal_donate_id = %s",
                        args=[kwargs['status'], user_list[i]]
                    )
                db.commit()
                return True
            else:
                return False
        else:
            return False
    else:
        return False

