from django.contrib.auth.models import BaseUserManager

class CustomerUserManager(BaseUserManager):

    def create_user(self, name, email, password=None, **extra_fields):

        if not name:
            raise ValueError("Users must have a name.")
        if not email:
            raise ValueError("Users must have an email.")

        email = self.normalize_email(email)
        user = self.model(
            name=name,
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, name, email, password, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            name=name,
            email=email,
            password=password,
            **extra_fields
        )
