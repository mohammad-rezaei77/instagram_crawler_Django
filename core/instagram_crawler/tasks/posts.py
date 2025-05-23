import datetime
import logging

import requests
from celery import shared_task
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

from instagram_crawler.models import Log, Post, PostItem, Session

logger = logging.getLogger()


PROXY = f"{'http://89.238.132.188'}:{'3128'}"

def get_and_validate_best_session():
    print("get_and_validate_best_session...")
    """
    Retrieve the best session and validate it.
    If valid, returns the session.
    If invalid, returns None.
    :return: A Client instance or None
    """
    try:

        session = Session.objects.get_best_session()
        if not session:
            print("No session found. Please create a new session.")
            return None

        print(f"Checking validity of session for username: {session.username}")
        
        cl = Client()
        cl.set_proxy(PROXY)

        # Configure the client with session data
        cl.set_settings(session.session_data)

        # Test session validity by retrieving timeline information
        cl.get_timeline_feed()
        print(f"Session is valid for user: {session.username}")

        session.custom_update()

        return cl

    except Exception as e:
        print(f"Session is invalid: {e}")
        Log.objects.create(spot="Session is invalid:", content=str(e))
        
        # Mark the session as invalid
        if session:
            session.hit_challenge()

        # Callback to try the next best session
        return get_and_validate_best_session()


def is_profile_private(cl, username):
    print("is_profile_private...")
    try:
        user_id = cl.user_id_from_username(username)
        user_info = cl.user_info(user_id)
        Log.objects.create(spot="is_profile_private", content=f"username:{user_info.is_private}")
        
        return user_info.is_private
    except Exception as e:
        Log.objects.create(spot="Err_is_profile_private", content=f"error {username}, {str(e)} ")
        print(f"Error: {e}")
        return None


def fetch_page(item_id, requested_posts):
    fetch_and_store_posts.delay(item_id, requested_posts)
    return "Starting the post fetching operation"


@shared_task
def fetch_and_store_posts(item_id, requested_posts):
    """
    Get the best session, validation, and post storage for the specified user.
    """
    requested_posts = int(requested_posts)
    try:
        start_time = datetime.datetime.now()
        # Step 1: Get and validate the best session
        cl = get_and_validate_best_session()  # Reference to validation function
        if not cl:
            raise Exception(
                "No valid session found or session is invalid. Please create a session first."
            )

        # adds a random delay between 3 and 6 seconds after each request
        cl.delay_range = [3, 10]

        # Save the post in the database model
        post_obj = Post.objects.filter(id=item_id).first()
        if not post_obj:
            raise Exception(f"post_obj with id {item_id} not found.")

        current_post = {}

        profile_info = cl.user_info_by_username(post_obj.profile)
        medias_count = int(profile_info.media_count)
        item_per_page = 20

        user_id = cl.user_id_from_username(post_obj.profile)
        end_cursor = None

        if requested_posts == 0 :
            remaining_posts = medias_count
        else:
            remaining_posts = requested_posts
            
        remaining_posts= int(remaining_posts)
        all_posts = []
        while remaining_posts > 0:            
            fetch_count = min(item_per_page, remaining_posts)
            posts, end_cursor = cl.user_medias_paginated(
                user_id, fetch_count, end_cursor=end_cursor
            )
            all_posts.extend(posts)
            remaining_posts -= len(posts)
            
            if not end_cursor:
                break  
        for post in all_posts:

            current_post = {
                "post_pk": post.pk,
                "caption": post.caption_text,
                "likes": post.like_count,
                "comments": post.comment_count,
                "usertags": [item.user.username for item in post.usertags],
                "view_count": post.view_count,
                "type": post.media_type,
                "product_type": post.product_type,
                "thumbnail_url": str(post.thumbnail_url),
                "video_url": str(post.video_url),
                "media": [
                    {
                        "type": (
                            "Photo"
                            if resource.media_type == 1
                            else (
                                "Video"
                                if resource.media_type == 2
                                else (
                                    "Album"
                                    if resource.media_type == 8
                                    else "unknown"
                                )
                            )
                        ),
                        "thumbnail_url": str(resource.thumbnail_url),
                        "Video": str(resource.video_url),
                    }
                    for resource in post.resources
                ],
            }
            PostItem.objects.create(post=post_obj, content=current_post)
            # remaining_posts -= fetch_count

                # post_obj.post_data.update(current_post)
            # medias_count -= item_per_page
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        post_obj.loading_time = duration
        post_obj.save()
        
        logger.info(
            f"Successfully fetched and stored {len(posts)} posts for user: {post_obj.profile}"
        )

    except LoginRequired as e:
        logger.error("Session login required: %s", e)

    except Exception as e:
        logger.error("Error during fetching posts: %s", e)


def fetch_single_post_data(post_url):
    """
    Get the best session, validation, and get single post for the specified URL.
    """
    cl = get_and_validate_best_session()  # Reference to validation function
    if not cl:
        raise Exception(
            "No valid session found or session is invalid. Please create a session first."
        )

    try:
        # Fetch post information
        media_id = cl.media_pk_from_url(post_url)
        post = cl.media_info(media_id)

        if post.user.is_private:
            raise Exception("This account is private, and you don't have access.")
            
        current_post = {
            "post_pk": post.pk,
            "caption": post.caption_text,
            "likes": post.like_count,
            "comments": post.comment_count,
            "usertags": [item.user.username for item in post.usertags],
            "view_count": post.view_count,
            "reels": str(post.video_url) if post.video_url else None,
            "type": post.media_type,
            "product_type": post.product_type,
            "thumbnail_url": str(post.thumbnail_url),
            "video_url": str(post.video_url),
            "media": [
                {
                    "type": (
                        "Photo"
                        if resource.media_type == 1
                        else (
                            "Video"
                            if resource.media_type == 2
                            else ("Album" if resource.media_type == 8 else "unknown")
                        )
                    ),
                    "thumbnail_url": str(resource.thumbnail_url),
                    "Video": str(resource.video_url),
                }
                for resource in post.resources
            ],
        }
        return current_post

    except Exception as e:
        logger.error("Failed to fetch post details:%s", e)

def fetch_user_info(user_name):
    cl = get_and_validate_best_session()  # Reference to validation function
    if not cl:
        raise Exception(
            "No valid session found or session is invalid. Please create a session first."
        )
    user_info = cl.user_info_by_username(user_name)
    user_information = {
        "profile_pic_url":str(user_info.profile_pic_url),
        "full_name": user_info.full_name,
        "followers_count": user_info.follower_count ,
        "following_count": user_info.following_count,
        "media_count": user_info.media_count,
        "biography": user_info.biography ,
        "external_url": user_info.external_url,
        "is_private": user_info.is_private,
    }
    return user_information

    