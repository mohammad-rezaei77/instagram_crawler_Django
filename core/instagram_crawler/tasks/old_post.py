import time

from celery import shared_task
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RecaptchaChallengeForm,
    SelectContactPointRecoveryForm,
)

from instagram_crawler.models import Log, Post, Session


class InstagramDataFetcher:
    def __init__(self, proxy_ip="http://89.238.132.188", proxy_port="3128"):
        try:
            # Initialize session
            self.session = Session.objects.get_best_session()
            if not self.session:
                raise ValueError("No valid session found.")

            # Set up proxy
            self.set_proxy = f"{proxy_ip}:{proxy_port}"
            self.client = Client()
            # self.client.set_proxy(self.set_proxy)
            self.client.set_settings(self.session.session_data)
            self.client.delay_range = [1, 50]
            self.logged_in = False

            # Try to login
            self.login()

        except ConnectionError as e:
            print("Error: Unable to connect to proxy server.", e)
            self.logged_in = False
        except Exception as e:
            print("An unexpected error occurred:", e)
            self.logged_in = False

    def login(self):
        print("start login...")
        USERNAME = self.session.username
        PASSWORD = self.session.password
        content = ""
        try:
            self.client.login(USERNAME, PASSWORD)
            self.logged_in = True
            try:
                self.client.get_timeline_feed()
            except LoginRequired:
                print("Session is invalid, need to login via username and password")
                old_session = self.client.get_settings()

                self.client.set_settings({})
                self.client.set_uuids(old_session["uuids"])

                self.client.login(USERNAME, PASSWORD)
            # login_via_session = True
        except Exception as e:
            # If Password Is Wrong
            if isinstance(e, BadPassword):
                print("BadPassword")
                self.client.logger.exception(e)

                Log.log_error(
                    spot="store_instagram_login", content=f"Wrong Password: {e}"
                )

                self.session.hit_challenge()
                self.session = Session.objects.get_best_session()
                self.client.set_settings(self.session.session_data)
                self.login()

            # If Login Required
            elif isinstance(e, LoginRequired):
                print("LoginRequired")
                self.client.logger.exception(e)
                self.client.relogin()

                Log.log_error(
                    spot="store_instagram_login", content=f"Login Required: {e}"
                )

                self.session.hit_challenge()
                self.session = Session.objects.get_best_session()
                self.client.set_settings(self.session.session_data)
                self.login()

            # If We Hit The Challenge
            elif isinstance(e, ChallengeRequired):
                print("ChallengeRequired")
                try:
                    self.client.challenge_resolve(self.client.last_json)
                except ChallengeRequired as e:
                    content = f"Challenge Required: {e}"
                except (
                    ChallengeRequired,
                    SelectContactPointRecoveryForm,
                    RecaptchaChallengeForm,
                ) as e:
                    content = f"Challenge, Recaptcha Required: {e}"

                Log.log_error(spot="store_instagram_login", content=content)
                self.session.hit_challenge()
                self.session = Session.objects.get_best_session()
                self.client.set_settings(self.session.session_data)
                self.login()

            # If We Need To Send Feed Back
            elif isinstance(e, FeedbackRequired):
                print("FeedbackRequired")

                message = self.client.last_json["feedback_message"]
                if "This action was blocked. Please try again later" in message:
                    content = f"Action Blocked, Freeze For 12 Hour: {e}"

                elif "We restrict certain activity to protect our community" in message:
                    # 6 hours is not enough
                    content = f"Action Blocked 2, Freeze For 12 Hour: {e}"

                elif "Your account has been temporarily blocked" in message:
                    """
                    Based on previous use of this feature, your account has been temporarily
                    blocked from taking this action.
                    This block will expire on 2020-03-27.
                    """
                    content = f"Action Blocked: {e}"
                Log.log_error(spot="store_instagram_login", content=content)
                self.session.temp_block()
                self.session = Session.objects.get_best_session()
                self.client.set_settings(self.session.session_data)
                self.login()

            # If Need To Wait Few Minutes
            elif isinstance(e, PleaseWaitFewMinutes):
                print("PleaseWaitFewMinutes")
                Log.log_error(
                    spot="store_instagram_login", content=f"Wait Few Minutes:{e}"
                )
                self.session.temp_block()
                self.session = Session.objects.get_best_session()
                self.client.set_settings(self.session.session_data)
                self.login()

            # We Blocked
            else:
                print("We Blocked")

                Log.log_error(spot="except-login-insta", content=f"Couldn't login: {e}")
                self.session.block()
                self.session = Session.objects.get_best_session()
                self.client.set_settings(self.session.session_data)
                self.login()

    def fetch_posts(self, page_id, profile_username):

        print(f"starting fetch_posts:{profile_username}...")
        start_time = time.time()
        try:
            insta_post = Post.objects.filter(id=page_id).first()
            insta_post.session = self.session

            if self.logged_in:
                profile_info = self.client.user_info_by_username(profile_username)
                user_id = self.client.user_id_from_username(profile_username)
                medias_count = profile_info.media_count
                print(f"medias_count:{medias_count}")

                # notify the session used once again
                self.session.custom_update()

                end_cursor = None
                all_posts = []
                item_per_page = 20
                while medias_count > 0:
                    medias, end_cursor = self.client.user_medias_paginated(
                        user_id, item_per_page, end_cursor=end_cursor
                    )

                    for post in medias:
                        current_post = {
                            "post_id": post.pk,
                            "caption": post.caption_text,
                            "likes": post.like_count,
                            "comments": post.comment_count,
                            "reels": str(post.video_url),
                            "type": post.media_type,
                            "media": [
                                {
                                    "type": (
                                        "img"
                                        if resource.media_type == 1
                                        else (
                                            "view"
                                            if resource.media_type == 2
                                            else "igtv"
                                        )
                                    ),
                                    "thumbnail_url": str(
                                        resource.thumbnail_url
                                        if resource.media_type == 1
                                        else resource.video_url
                                    ),
                                    "video_url": (
                                        str(resource.video_url)
                                        if resource.media_type != 1
                                        else None
                                    ),
                                }
                                for resource in post.resources
                            ],
                        }
                        Log.log_error(spot="current_post", content=current_post)

                        all_posts.append(current_post)
                    medias_count -= item_per_page

                    existing_json_data = insta_post.post_data or []

                    # print(f"OLD POSTS : {existing_json_data}")

                    # Append New Json To Old One

                    existing_json_data.append(all_posts)
                    # print(f"NEW POSTS : {existing_json_data}")

                    # Update Post
                    insta_post.post_data = existing_json_data[-1]

                    end_time = time.time()
                    loading_time = end_time - start_time
                    insta_post.loading_time = loading_time

                    insta_post.save()

                return True
            else:
                print("------------------------------logged_in else")
                Log.log_error(spot="insta-fetch-posts", content="Not authenticated!")
                return False
        except Exception as e:
            Log.log_error(
                spot="except-insta-fetch-posts", content=f"Couldn't fetch posts: {e}"
            )
            return False


@shared_task
def fetch_profile_data(page_id):
    start_time = time.time()
    post = Post.objects.filter(id=page_id).first()
    insta_data_fetcher = InstagramDataFetcher()
    insta_data_fetcher.fetch_posts(page_id, post.profile)

    end_time = time.time()
    loading_time = end_time - start_time
    print(f"Execution time: {loading_time} seconds.")
