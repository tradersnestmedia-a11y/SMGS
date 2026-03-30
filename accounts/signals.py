from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            role=UserProfile.ROLE_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT,
        )
    else:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={"role": UserProfile.ROLE_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT},
        )
