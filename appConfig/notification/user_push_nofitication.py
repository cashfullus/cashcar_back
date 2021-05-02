from firebase_admin import messaging


def send_to_one_firebase_cloud_messaging(token, title, notification):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=notification,
        ),
        token=token,
    )

    response = messaging.send(message)
    return response

#
# def send_to_many_firebase_cloud_messaging(tokens, title, notification):
#     message = messaging.MulticastMessage(
#         data
#     )