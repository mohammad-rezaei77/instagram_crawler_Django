from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class SessionManager(models.Manager):
    def get_best_session(self):
        print("get_best_session")
        return (
            self.filter(is_block=False)
            .filter(is_challenge=False)
            .filter(is_temp_block=False)
            .order_by("number_of_use")
            .first()
        )


class Session(models.Model):
    username = models.CharField(max_length=250, blank=False, null=False)
    password = models.CharField(max_length=250, blank=False, null=False)
    session_data = models.JSONField(null=True, blank=True)

    is_block = models.BooleanField(default=False)
    is_temp_block = models.BooleanField(default=False)
    is_challenge = models.BooleanField(default=False)
    number_of_use = models.IntegerField(default=0)

    create_at = models.DateTimeField(auto_now_add=True)
    last_use_at = models.DateTimeField(null=True, blank=True)

    objects = SessionManager()

    def __str__(self):
        return str(self.username)

    def custom_update(self):
        self.number_of_use += 1
        self.last_use_at = timezone.now()
        self.save()

    def hit_challenge(self):
        self.is_challenge = True
        self.save()

    def block(self):
        self.is_block = True
        self.save()

    def temp_block(self):
        self.is_temp_block = True
        self.save()


@receiver(post_save, sender=Session)
def create_session_on_save(sender, instance, created, **kwargs):

    if created:
        pass
        # from .tasks import create_session
        # create_session.delay(instance.username)


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(Session, null=True, on_delete=models.CASCADE)
    post_data = models.JSONField(null=True, blank=True)
    profile = models.CharField(max_length=250, null=True, blank=True)

    loading_time = models.CharField(max_length=250)
    create_at = models.DateTimeField(auto_now_add=True)

    def fill_object(self, session, json_posts, *args, **kwargs):
        self.session = Session.objects.filter(pk=session.id).first()
        self.json_posts = json_posts
        self.save()


class log(models.Model):
    content = models.TextField()
    spot = models.CharField(max_length=250)
    create_date = models.DateTimeField(auto_now_add=True)

    @classmethod
    def log_error(cls, content, spot):
        return cls.objects.create(content=content, spot=spot)
