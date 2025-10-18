from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RegisteredUser, User


@receiver(post_save, sender=RegisteredUser)
def create_ml_user(sender, instance, created, **kwargs):
    if created:
        User.objects.get_or_create(
            user_id=str(instance.id),  # or instance.username if preferred
            defaults={
                "age": None,
                "location": ""
            }
        )
        print(f"✅ ML user created for RegisteredUser: {instance.username}")
