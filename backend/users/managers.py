from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):

    def create_superuser(self,
                         username,
                         email=None,
                         password=None,
                         **extra_fields
                         ):
        super_user = super().create_superuser(
            username, email, password, **extra_fields
        )
        super_user.role = 'admin'
        super_user.save()
        return super_user
