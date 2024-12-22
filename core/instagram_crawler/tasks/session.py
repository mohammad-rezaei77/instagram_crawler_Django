from celery import shared_task
from instagrapi import Client

from instagram_crawler.models import Session


def create_and_save_session(username):
    cl = Client()

    # cl.set_locale("en_US")  # تنظیم زبان
    # cl.set_timezone_offset(19800)  # منطقه زمانی هند، به عنوان مثال (+5:30)

    try:
        session = Session.objects.get(username=username)

        # ورود با نام کاربری و رمز عبور
        cl.login(session.username, session.password)


        # ذخیره نشست
        session_data = cl.get_settings()

        # ذخیره اطلاعات در مدل
        session.session_data = session_data
        session.save()
        print(f"Session created and stored for user: {username}")

    except Exception as e:
        print(str(e))
        if "challenge" in str(e):
            print("Verification required. Enter the code sent to your email/phone.")
            code = input("Enter verification code: ")
            cl.challenge_resolve(code)

            # ذخیره نشست بعد از تأیید
            session_data = cl.get_settings()
            session.session_data = session_data

            session.save()
            print(f"Session created and stored for user: {username}")
        else:
            print(f"Error during login: {e}")


@shared_task
def create_session(username):
    print("starting create_session")

    proxy_ip = "http://89.238.132.188"
    proxy_port = "3128"
    set_proxy = f"{proxy_ip}:{proxy_port}"

    cl = Client()
    # cl.set_proxy(set_proxy)
    obj = Session.objects.get(username=username)
    cl.login(obj.username, obj.password, obj.code)
    session_data = cl.get_settings()
    obj.session_data = session_data
    obj.save()
    print("update session successfully")
