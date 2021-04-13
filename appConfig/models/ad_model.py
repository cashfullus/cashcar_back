from ..database.dbConnection import Database
import os

BASE_IMAGE_LOCATION = os.getcwd() + "/appConfig/static/image/adverting"


def register(image_dict, **kwargs):
    db = Database()
    sql = "INSERT INTO ad_information " \
          "(title, recurit_start_date, recurit_end_date, activity_period, " \
          "recuriting_count, area, description, " \
          "sticker_design_side_size, sticker_design_back_size) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    kwargs['recurit_start_date'] = kwargs['recurit_start_date'] + " 00:00:00"
    kwargs['recurit_end_date'] = kwargs['recurit_end_date'] + " 23:59:59"
    # value_list = [kwargs['title'], kwargs['recuirt_start_date'], kwargs['recurit_end_date']]
    # result = db.execute(query=sql, args=[kwargs['title'], ])
    # sql = "INSERT INTO ad_information " \
    #       "(title, title_image, logo_image, recurit_start_date, recurit_end_date, " \
    #       "activity_period, recuriting_count, area, description, sticker_design_side_image, " \
    #       "sticker_design_back_image, sticker_attach_side_image, sticker_attach_back_image, " \
    #       "sticker_design_side_size, sticker_design_back_size) " \
    #       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    return kwargs
    # value_list = [kwargs['title'], image_dict['title_image'], image_dict['logo_image']]

