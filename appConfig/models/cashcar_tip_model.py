from database.dbConnection import Database
from werkzeug.utils import secure_filename

import os

BASE_IMAGE_LOCATION = os.getcwd() + "/static/image/cash_car_tip"
CASH_CAR_TIP_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/cash_car_tip"


def save_tip_images(cash_car_tip_id, **kwargs):
    db = Database()
    directory = f"{BASE_IMAGE_LOCATION}/{cash_car_tip_id}"
    kwargs['thumbnail_image'].save(directory + "/" + secure_filename(kwargs['thumbnail_image'].filename))
    order_cnt = 1
    for i in range(len(kwargs['tip_images'])):
        image = kwargs['tip_images'][i]
        db_url = f"{CASH_CAR_TIP_IMAGE_HOST}/{cash_car_tip_id}/{secure_filename(image.filename)}"
        os.makedirs(directory, exist_ok=True)
        image.save(directory + "/" + secure_filename(image.filename))
        db.execute(
            query="INSERT INTO cash_car_tip_images (cash_car_tip_id, image, `order`) VALUE "
                  "(%s, %s, %s)",
            args=[cash_car_tip_id, db_url, order_cnt]
        )
        order_cnt += 1
    db.commit()
    return True


def tip_info_response_data(cash_car_tip_id):
    db = Database()
    response_data = db.executeOne(
        query="SELECT cash_car_tip_id, title, thumbnail_image, main_description, "
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM cash_car_tip WHERE cash_car_tip_id = %s",
        args=cash_car_tip_id
    )
    images = db.executeAll(
        query="SELECT image FROM cash_car_tip_images WHERE cash_car_tip_id = %s",
        args=cash_car_tip_id
    )
    response_data['image_information'] = images
    return response_data


def register(**kwargs):
    db = Database()
    db.execute(
        query="INSERT INTO cash_car_tip (title, main_description) "
              "VALUES (%s, %s)",
        args=[kwargs.get('title'), kwargs.get('main_description')]
    )
    last_insert_id = db.executeOne(
        query="SELECT cash_car_tip_id FROM cash_car_tip ORDER BY register_time DESC LIMIT 1"
    )['cash_car_tip_id']
    db.commit()
    save_tip_images(cash_car_tip_id=last_insert_id, **kwargs)
    thumbnail_url = f"{CASH_CAR_TIP_IMAGE_HOST}/{last_insert_id}/{secure_filename(kwargs['thumbnail_image'].filename)}"
    db.execute(
        query="UPDATE cash_car_tip SET thumbnail_image = %s WHERE cash_car_tip_id = %s",
        args=[thumbnail_url, last_insert_id]
    )
    db.commit()
    result = tip_info_response_data(cash_car_tip_id=last_insert_id)
    return result


# 캐시카팁 리스트
def get_cash_car_tip_all(page, request_user, count=10):
    db = Database()
    per_page = (page - 1) * count
    if request_user == "user":
        cash_car_tip_information = db.executeAll(
            query="SELECT cash_car_tip_id, title, thumbnail_image, main_description, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM cash_car_tip ORDER BY register_time DESC LIMIT %s OFFSET %s",
            args=[count, per_page]
        )
        return cash_car_tip_information
    else:
        cash_car_tip_information = db.executeAll(
            query="SELECT cash_car_tip_id, title, thumbnail_image, main_description, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM cash_car_tip ORDER BY register_time DESC LIMIT %s OFFSET %s",
            args=[count, per_page]
        )
        if cash_car_tip_information:
            for i in range(len(cash_car_tip_information)):
                images = db.executeAll(
                    query="SELECT image FROM cash_car_tip_images WHERE cash_car_tip_id = %s ORDER BY `order`",
                    args=cash_car_tip_information[i]['cash_car_tip_id']
                )
                cash_car_tip_information[i]['image_information'] = images
        item_count = db.executeOne(
            query="SELECT count(cash_car_tip_id) as item_count FROM cash_car_tip"
        )['item_count']
        return cash_car_tip_information, item_count


def get_cash_car_tip_by_id(cash_car_tip_id):
    db = Database()
    non_result = {
        "cash_car_tip_id": -1,
        "title": "",
        "thumbnail_image": "",
        "main_description": "",
        "register_time": "",
        "image_information": []
    }
    result = db.executeOne(
        query="SELECT cash_car_tip_id, title, thumbnail_image, main_description, "
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM cash_car_tip WHERE cash_car_tip_id = %s ORDER BY register_time DESC",
        args=cash_car_tip_id
    )
    if not result:
        return non_result
    else:
        images = db.executeAll(
            query="SELECT image FROM cash_car_tip_images WHERE cash_car_tip_id = %s ORDER BY `order`",
            args=cash_car_tip_id
        )
        result['image_information'] = images
        return result


# 캐시카팁 수정
def modify_cash_car_tip(cash_car_tip_id, **kwargs):
    db = Database()
    tip_info = db.getOneCashCarTipById(cash_car_tip_id=cash_car_tip_id)
    if tip_info:
        thumbnail_url = f"{CASH_CAR_TIP_IMAGE_HOST}/{cash_car_tip_id}/" \
                        f"{secure_filename(kwargs['thumbnail_image'].filename)}"
        db.execute(
            query="UPDATE cash_car_tip SET title = %s, main_description = %s, thumbnail_image = %s "
                  "WHERE cash_car_tip_id = %s",
            args=[kwargs.get('title'), kwargs.get('main_description'), thumbnail_url, cash_car_tip_id]
        )
        db.commit()
        save_tip_images(cash_car_tip_id=cash_car_tip_id, **kwargs)
        result = tip_info_response_data(cash_car_tip_id=cash_car_tip_id)
        return result
    else:
        return False


# 캐시카팁 삭제
def delete_cash_car_tip(cash_car_tip_id):
    db = Database()
    tip_info = db.getOneCashCarTipById(cash_car_tip_id=cash_car_tip_id)
    directory = f"{BASE_IMAGE_LOCATION}/{cash_car_tip_id}"
    os.remove(directory)
    if tip_info:
        db.execute(
            query="DELETE FROM cash_car_tip WHERE cash_car_tip_id = %s",
            args=cash_car_tip_id
        )
        db.execute(
            query="DELETE FROM cash_car_tip_images WHERE cash_car_tip_id = %s",
            args=cash_car_tip_id
        )
        db.commit()
        return True
    else:
        return False
