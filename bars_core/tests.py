from rest_framework.test import APITestCase
from bars_django.utils import get_root_bar
from bars_core.models.bar import Bar, BarSerializer, BarSettingsSerializer
from bars_core.models.user import User, UserSerializer
from bars_core.models.role import Role
from bars_core.models.account import Account, AccountSerializer


def reload(obj):
    return obj.__class__.objects.get(pk=obj.pk)


class BackendTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(BackendTests, self).setUpTestData()
        User.objects.create_user("test", "test")


    def test_login(self):
        data = {'username': 'test', 'password': 'test'}
        response = self.client.post('/api-token-auth/', data, format='json')

        self.assertEqual(response.status_code, 200)

        token = response.data["token"]
        auth = 'JWT {0}'.format(token)
        response = self.client.get('/user/me/', HTTP_AUTHORIZATION=auth, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], "test")

    def test_login_wrong_password(self):
        data = {'username': 'test', 'password': 'sdgez'}
        response = self.client.post('/api-token-auth/', data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_login_wrong_user(self):
        data = {'username': 'not_admin', 'password': 'test'}
        response = self.client.post('/api-token-auth/', data, format='json')

        self.assertEqual(response.status_code, 400)


    def test_add_superuser(self):
        u = User.objects.create_superuser("su", "su")
        self.assertTrue(u.is_superuser)
        self.assertTrue(u.is_staff)



class BarTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(BarTests, self).setUpTestData()
        get_root_bar._cache = None  # Workaround
        root_bar = get_root_bar()
        self.manager, _ = User.objects.get_or_create(username="manager")
        Role.objects.get_or_create(bar=root_bar, user=self.manager, name="admin")
        self.manager = reload(self.manager)  # prevent role caching

        self.bar, _ = Bar.objects.get_or_create(id="barrouje")

        serializer = BarSerializer(self.bar)
        self.data = serializer.data
        self.data['name'] = "barjone"
        self.bar_url = '/bar/%s/' % self.bar.id

    def setUp(self):
        self.bar.name = "barrouje"
        self.bar.save()


    def test_get_bar_not_authed(self):
        # Not authenticated
        response = self.client.get(self.bar_url)
        self.assertEqual(response.status_code, 200)

    def test_get_bar_authed(self):
        # Authenticated
        self.client.force_authenticate(user=User())
        response = self.client.get(self.bar_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.bar.name)


    def test_change_bar_no_perms(self):
        # Not authenticated
        self.client.force_authenticate(user=User())
        response = self.client.put(self.bar_url, self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_bar_admin(self):
        # Authenticated as manager
        self.client.force_authenticate(user=self.manager)
        response = self.client.put(self.bar_url, self.data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(reload(self.bar).name, self.data['name'])


class BarSettingsTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(BarSettingsTests, self).setUpTestData()
        self.bar, _ = Bar.objects.get_or_create(id="barjone")
        self.manager, _ = User.objects.get_or_create(username="manager")
        self.manager.role_set.all().delete()
        Role.objects.get_or_create(bar=self.bar, user=self.manager, name="staff")
        self.manager = reload(self.manager)  # prevent role caching

        self.barsettings = self.bar.settings

        serializer = BarSettingsSerializer(self.barsettings)
        self.data = serializer.data
        del self.data['next_scheduled_appro']
        self.data['agios_enabled'] = True
        self.barsettings_url = '/barsettings/%s/' % self.barsettings.pk

    def setUp(self):
        self.barsettings.agios_enabled = False
        self.barsettings.save()


    def test_get_not_authed(self):
        # Not authenticated
        response = self.client.get(self.barsettings_url)
        self.assertEqual(response.status_code, 200)

    def test_get_authed(self):
        # Authenticated
        self.client.force_authenticate(user=User())
        response = self.client.get(self.barsettings_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reload(self.barsettings).agios_enabled, response.data['agios_enabled'])


    def test_change_no_perms(self):
        # Not authenticated
        self.client.force_authenticate(user=User())
        response = self.client.put(self.barsettings_url, self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_admin(self):
        # Authenticated as manager
        self.client.force_authenticate(user=self.manager)
        response = self.client.put(self.barsettings_url, self.data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(reload(self.barsettings).agios_enabled, self.data['agios_enabled'])


class UserTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(UserTests, self).setUpTestData()
        get_root_bar._cache = None  # Workaround
        root_bar = get_root_bar()
        self.manager, _ = User.objects.get_or_create(username="manager")
        Role.objects.get_or_create(bar=root_bar, user=self.manager, name="admin")
        self.manager = reload(self.manager)  # prevent role caching

        self.user, _ = User.objects.get_or_create(username="bob")
        self.user.set_password("password")
        self.user.email = "bob@chocapix.org"
        self.user.save()

        serializer = UserSerializer(self.user)
        self.data = serializer.data
        self.user_url = '/user/%d/' % self.user.id

    def setUp(self):
        self.data['username'] = "bob"
        self.data['email'] = "bob@chocapix.org"
        self.user.username = "bob"
        self.user.save()


    def test_get_user_not_authed(self):
        # Not authenticated
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, 401)

    def test_get_user_authed(self):
        # Authenticated
        self.client.force_authenticate(user=User())
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], self.data['username'])


    def test_create_user_no_perms(self):
        # Not authenticated
        data = {'username': "charles1"}
        self.client.force_authenticate(user=User())
        response = self.client.post('/user/', data)
        self.assertEqual(response.status_code, 403)

    def test_create_user_admin(self):
        # Authenticated as admin
        data = {'username': "charles2", 'email': "blabla@m4x.org"}
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/user/', data)
        self.assertEqual(response.status_code, 201)


    def test_change_user_no_perms(self):
        # Not authenticated
        self.client.force_authenticate(user=User())
        self.data['username'] = 'alice'
        response = self.client.put(self.user_url, self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_user_admin(self):
        # Authenticated as manager
        self.data['username'] = 'alice'
        self.client.force_authenticate(user=self.manager)
        response = self.client.put(self.user_url, self.data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(reload(self.user).username, self.data['username'])

    def test_change_user_self(self):
        # Authenticated as self
        self.data['username'] = 'alice'
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.user_url, self.data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(reload(self.user).username, self.data['username'])


    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        self.assertTrue(self.user.check_password('password'))

        data = {'old_password': 'password', 'password': '123456'}
        response = self.client.put('/user/change_password/', data)
        self.assertEqual(response.status_code, 200)

        user_reloaded = User.objects.get(pk=self.user.pk)
        self.assertTrue(user_reloaded.check_password('123456'))

    def test_change_password_wrong_password(self):
        self.client.force_authenticate(user=self.user)
        data = {'old_password': 'wrong_password', 'password': '123456'}
        response = self.client.put('/user/change_password/', data)
        self.assertEqual(response.status_code, 403)


class AccountTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(AccountTests, self).setUpTestData()
        self.bar, _ = Bar.objects.get_or_create(id='natationjone')
        Bar.objects.get_or_create(id='avironjone')

        self.user, _ = User.objects.get_or_create(username='nadrieril')
        self.user2, _ = User.objects.get_or_create(username='ntag')
        Role.objects.get_or_create(name='admin', bar=self.bar, user=self.user2)
        self.user2 = reload(self.user2)

        self.create_data = {'owner': self.user2.id}
        self.account, _ = Account.objects.get_or_create(owner=self.user, bar=self.bar)
        self.update_data = AccountSerializer(self.account).data
        self.update_data['deleted'] = True

    def setUp(self):
        self.account.deleted = False
        self.account.save()


    def test_get_account(self):
        response = self.client.get('/account/')
        self.assertEqual(len(response.data), Account.objects.all().count())
        self.assertEqual(response.data[0]['deleted'], self.account.deleted)


    def test_create_account(self):
        # Unauthenticated
        response = self.client.post('/account/?bar=natationjone', self.create_data)
        self.assertEqual(response.status_code, 401)

    def test_create_account1(self):
        # Wrong permissions
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/account/?bar=natationjone', self.create_data)
        self.assertEqual(response.status_code, 403)

    def test_create_account2(self):
        # Correct permissions
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/account/?bar=natationjone', self.create_data)
        self.assertEqual(response.status_code, 201)

    def test_create_account3(self):
        # Wrong bar
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/account/?bar=avironjone', self.create_data)
        self.assertEqual(response.status_code, 403)


    def test_change_account(self):
        # Unauthenticated
        response = self.client.put('/account/%d/?bar=natationjone' % self.account.id, self.update_data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(reload(self.account).deleted, self.account.deleted)

    def test_change_account2(self):
        # Wrong permissions
        self.client.force_authenticate(user=self.user)
        response = self.client.put('/account/%d/?bar=natationjone' % self.account.id, self.update_data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(reload(self.account).deleted, self.account.deleted)

    def test_change_account4(self):
        # Correct permissions
        self.client.force_authenticate(user=self.user2)
        response = self.client.put('/account/%d/?bar=natationjone' % self.account.id, self.update_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reload(self.account).deleted, self.update_data['deleted'])

    def test_change_account5(self):
        # Wrong bar
        self.client.force_authenticate(user=self.user2)
        response = self.client.put('/account/%d/?bar=avironjone' % self.account.id, self.update_data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(reload(self.account).deleted, self.account.deleted)



class RoleTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(RoleTests, self).setUpTestData()
        get_root_bar._cache = None  # Workaround

        self.bar, _ = Bar.objects.get_or_create(id='natationjone')
        Bar.objects.get_or_create(id='avironjone')

        self.user, _ = User.objects.get_or_create(username='nadrieril')
        self.user2, _ = User.objects.get_or_create(username='ntag')
        self.root, _ = User.objects.get_or_create(username='root')

        Role.objects.get_or_create(name='admin', bar=self.bar, user=self.user2)
        self.user2 = reload(self.user2)
        Role.objects.get_or_create(name='admin', bar=get_root_bar(), user=self.root)
        self.root = reload(self.root)

        self.create_data = {'user': self.user.id, 'name': 'customer'}
        self.create_data_root = {'user': self.user.id, 'name': 'usermanager'}


    def test_get_role(self):
        response = self.client.get('/role/')
        self.assertEqual(len(response.data), Role.objects.count())


    def test_create_role(self):
        # Unauthenticated
        response = self.client.post('/role/?bar=natationjone', self.create_data)
        self.assertEqual(response.status_code, 401)

    def test_create_role1(self):
        # Wrong permissions
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/role/?bar=natationjone', self.create_data)
        self.assertEqual(response.status_code, 403)

    def test_create_role2(self):
        # Correct permissions
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/role/?bar=natationjone', self.create_data)
        self.assertEqual(response.status_code, 201)

    def test_create_role3(self):
        # Wrong bar
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/role/?bar=avironjone', self.create_data)
        self.assertEqual(response.status_code, 403)

    def test_create_role_root(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/role/?bar=root', self.create_data_root)
        self.assertEqual(response.status_code, 403)

    def test_create_role_root2(self):
        self.client.force_authenticate(user=self.root)
        response = self.client.post('/role/?bar=root', self.create_data_root)
        self.assertEqual(response.status_code, 201)
