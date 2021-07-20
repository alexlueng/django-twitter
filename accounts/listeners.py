def profile_changed(sender, instance, **kwargs):
    from .services import UserService
    UserService.invalidate_profile(instance.user_id)