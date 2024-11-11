from instagrapi import Client

from .models import Session


def create_session(username):
    print("starting create_session")

    # proxy_ip="http://170.64.207.199"
    # proxy_port="3128"
    # set_proxy = f"{proxy_ip}:{proxy_port}"

    cl = Client()
    # cl.set_proxy(set_proxy)
    obj = Session.objects.get(username=username)
    cl.login(obj.username, obj.password)
    session_data = cl.get_settings()
    obj.session_data = session_data
    obj.save()
    print("update session successfully")
