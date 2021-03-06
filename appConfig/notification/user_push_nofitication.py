from pyfcm import FCMNotification
push_service = FCMNotification("AAAAkXM-QLM:APA91bHwHI41QqjkSg4anW2H-K6JNWlT1wbdcOf2ptL_Uf045t6bhmu66b1NRjhmYkYR86KG4dH5aIUgSoRq47oZI5_hue7mRn_9hIvSxnDcQ2c9dSEInWcwsFdXZ3FNx1KQ4LmoShoJ")


def one_cloud_messaging(token, body, title=None):
    if title is None:
        result = push_service.notify_single_device(registration_id=token, message_body=body)
    else:
        result = push_service.notify_single_device(registration_id=token, message_title=title, message_body=body)
    return result


def multiple_cloud_messaging(tokens, body, title=None):
    if title is None:
        result = push_service.notify_multiple_devices(registration_ids=tokens, message_body=body)
    else:
        result = push_service.notify_multiple_devices(registration_ids=tokens, message_title=title, message_body=body)
    return result

# get_token = "e517fTcLSMyyRN1OFZPWB3:APA91bHQUtmSF-GGXEv8GzafcWhEnJ1ageHLFIP2SEwMJxUxy_8CovJTjfGbq8_gF3NIMeqyFqcu3T7WyJMrGaHApXPlt2g3CorV75jSzfiixSV9KcMaYRdSrrYnVt-_qxFVzzgwrLTA"
#
# print(one_cloud_messaging(token=get_token, body="치킨 공짜쿠폰", title="배달의 민족"))