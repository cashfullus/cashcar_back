from pyfcm import FCMNotification
push_service = FCMNotification("AAAAkXM-QLM:APA91bHwHI41QqjkSg4anW2H-K6JNWlT1wbdcOf2ptL_Uf045t6bhmu66b1NRjhmYkYR86KG4dH5aIUgSoRq47oZI5_hue7mRn_9hIvSxnDcQ2c9dSEInWcwsFdXZ3FNx1KQ4LmoShoJ")


def one_cloud_messaging(token, body, title):
    result = push_service.notify_single_device(registration_id=token, message_title=title, message_body=body)
    print(result)


def multiple_cloud_messaging(tokens, body, title):
    result = push_service.notify_multiple_devices(registration_ids=tokens, message_title=title, message_body=body)
    print(result)


app_push_token = "cXiJtS6v-UXLkYIGUnGe3_:APA91bEqSmKUxJpltrdhiOw6gQEZTZ_blqZhkovss1Fbb_uody2Hy2jNy-8u06FzSzMDwoN4ON3hfyAubt1Y9wcTY-4mf42DjfbW8VbDujp2bk2MsTRCF4b6G5Cm-UBQ8Ec7Y1Mtjnud"
app_tokens = ['cXiJtS6v-UXLkYIGUnGe3_:APA91bEqSmKUxJpltrdhiOw6gQEZTZ_blqZhkovss1Fbb_uody2Hy2jNy-8u06FzSzMDwoN4ON3hfyAubt1Y9wcTY-4mf42DjfbW8VbDujp2bk2MsTRCF4b6G5Cm-UBQ8Ec7Y1Mtjnud',
              'erdfA5HsRvK3xVoaIFlP2l:APA91bEPvDx_HQ7Qq1KOecABEGepVwbh2v9vnJ97cOUdFKJyi1rjkDHM8sXgtTloYiF-WjMXcHBSkwjJNpUj74R3DzH8C1unRalxJ0Eu6EMRihoxD76cM30lgqTTy8QEAzg3_daOwxpu']
one_cloud_messaging(token=app_push_token, body="배달의 민족", title="치킨 꽁짜 쿠폰!")
# multiple_cloud_messaging(tokens=app_tokens, body="배달의 민족", title="치킨 꽁짜 쿠폰!")