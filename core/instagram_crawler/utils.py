import json

from instagrapi import Client


def create_session(username, password):
    print("starting create_session")

    proxy_ip = "http://170.64.207.199"
    proxy_port = "3128"
    set_proxy = f"{proxy_ip}:{proxy_port}"

    cl = Client()
    cl.set_proxy(set_proxy)

    try:
        # تلاش برای ورود
        cl.login(username, password)
    except Exception as e:
        print(f"Error during login: {e}")
        # بررسی چالش در صورت نیاز
        if 'challenge' in str(e):
            print("Challenge detected. Waiting for code...")
            challenge_code = input("Enter the code sent to your email or phone: ")
            # ارسال کد چالش
            cl.challenge_api(challenge_code)
            print("Challenge passed successfully.")

    # دریافت تنظیمات سشن پس از ورود موفق
    session_data = cl.get_settings()

    # ذخیره داده‌ها در فایل JSON
    file_path = f"{username}_session_data.json"
    with open(file_path, 'w') as json_file:
        json.dump(session_data, json_file)

    print(f"Session data saved to {file_path} successfully")

# فراخوانی تابع با اطلاعات کاربری
create_session("winner_5008", "123456789B@")