from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
from rest_framework import viewsets, serializers, decorators
from rest_framework.response import Response

from bars_api.models import VirtualField


class UserManager(BaseUserManager):
    def create_user(self, username, password):
        user = self.model(username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        user = self.create_user(username, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    class Meta:
        app_label = 'bars_api'
    username = models.CharField(max_length=128, unique=True)
    full_name = models.CharField(max_length=128, blank=True)
    pseudo = models.CharField(max_length=128, blank=True)

    is_active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return self.full_name


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', '_type', 'username', 'full_name', 'pseudo', 'last_login', 'last_modified', 'password')
        write_only_fields = ('password',)
    _type = VirtualField("User")

    def restore_object(self, attrs, instance=None):
        user = super(UserSerializer, self).restore_object(attrs, instance)
        if 'password' in attrs:
            user.set_password(attrs['password'])
        return user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @decorators.list_route()
    def me(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
