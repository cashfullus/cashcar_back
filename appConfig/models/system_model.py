from database.dbConnection import Database


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
        return result
    if app_version:
        result["version"] = int(app_version['version'])
    return result
