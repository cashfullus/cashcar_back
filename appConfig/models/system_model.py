from database.dbConnection import Database
from werkzeug.utils import secure_filename

CASH_CAR_TIP_HOST = "https://app.api.service.cashcarplus.com:50193/image/cash_car_tip"

def get_app_version_check(device):
    db = Database()
    result = {"version": -1}
    if device == "ios":
        app_version = db.executeOne(
            query="SELECT ios_version as version FROM ios_release ORDER BY register_time DESC LIMIT 1"
        )
    elif device == "android":
        app_version = db.executeOne(
            query="SELECT android_version as version FROM android_release ORDER BY register_time DESC LIMIT 1"
        )
    else:
        db.db_close()
        return result
    if app_version:
        result["version"] = int(app_version['version'])
    db.db_close()
    return result


def delete_image(location, idx, image):
    db = Database()

    if location == "cash_car_tip":
        filename = f"{CASH_CAR_TIP_HOST}/{idx}/{secure_filename(image.filename)}"
        db.execute(
            query="DELETE FROM cash_car_tip_images WHERE image = %s",
            args=filename
        )
        db.commit()
        db.db_close()
        return True
    else:
        db.db_close()
        return False
