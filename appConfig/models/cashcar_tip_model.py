from database.dbConnection import Database
from werkzeug.utils import secure_filename

import os

BASE_IMAGE_LOCATION = os.getcwd() + "/static/image/cash_car_tip"
CASH_CAR_TIP_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/cash_car_tip"


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
    directory = f"{BASE_IMAGE_LOCATION}/{last_insert_id}"
    for i in range(len(kwargs.get('image_description'))):
        image = kwargs['tip_images'][i]
        db_url = f"{CASH_CAR_TIP_IMAGE_HOST}/{last_insert_id}/{secure_filename(image.filename)}"
        os.makedirs(directory, exist_ok=True)
        image.save(directory + "/" + secure_filename(image.filename))
        db.execute(
            query="INSERT INTO cash_car_tip_images (cash_car_tip_id, image, description) VALUE "
                  "(%s, %s, %s)",
            args=[last_insert_id, db_url, kwargs['image_description'][i]]
        )

    db.commit()
    response_data = db.executeOne(
        query="SELECT cash_car_tip_id, title, thumbnail_image, main_description, "
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM cash_car_tip WHERE cash_car_tip_id = %s",
        args=last_insert_id
    )
    images = db.executeAll(
        query="SELECT image, description FROM cash_car_tip_images WHERE cash_car_tip_id = %s",
        args=last_insert_id
    )
    response_data['image_information'] = images
    return response_data


def upload_thumbnail_image(image, tip_id):
    db = Database()
    db_url = f"{CASH_CAR_TIP_IMAGE_HOST}/{tip_id}/{secure_filename(image.filename)}"
    db.execute(
        query="UPDATE cash_car_tip SET thumbnail_image = %s WHERE cash_car_tip_id = %s",
        args=[db_url, tip_id]
    )
    directory = f"{BASE_IMAGE_LOCATION}/{tip_id}"
    image.save(directory + "/" + secure_filename(image.filename))
    db.commit()
    return True


def get_cash_car_tip_all(page, request_user, count=10):
    db = Database()
    per_page = (page-1) * count
    if request_user == "user":
        cash_car_tip_information = db.executeAll(
            query="SELECT cash_car_tip_id, title, thumbnail_image, main_description, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM cash_car_tip LIMIT %s OFFSET %s",
            args=[count, per_page]
        )
        return cash_car_tip_information
    else:
        cash_car_tip_information = db.executeAll(
            query="SELECT cash_car_tip_id, title, thumbnail_image, main_description, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM cash_car_tip LIMIT %s OFFSET %s",
            args=[count, per_page]
        )
        if cash_car_tip_information:
            for i in range(len(cash_car_tip_information)):
                images = db.executeAll(
                    query="SELECT image, description FROM cash_car_tip_images WHERE cash_car_tip_id = %s",
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
              "FROM cash_car_tip WHERE cash_car_tip_id = %s",
        args=cash_car_tip_id
    )
    if not result:
        return non_result
    else:
        images = db.executeAll(
            query="SELECT image, description FROM cash_car_tip_images WHERE cash_car_tip_id = %s",
            args=cash_car_tip_id
        )
        result['image_information'] = images
        return result
