# Generated by Django 5.1.2 on 2024-11-01 01:30

import accounts_app.models
import django.contrib.postgres.fields
import django.db.models.deletion
import django.utils.timezone
import django_countries.fields
import project.storage_backends
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailList',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_valid', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('phone_number', models.CharField(max_length=30)),
                ('is_shadchan', models.BooleanField(default=False)),
                ('is_single', models.BooleanField(default=False)),
                ('gender', models.IntegerField(blank=True, choices=[(1, 'Male'), (2, 'Female')], null=True)),
                ('stripe_customer_id', models.CharField(blank=True, help_text='The stripe customer id that is returned after a payment or when creating one with the stripe api we use this id to handle payments update payment methods ect.', max_length=255, null=True, unique=True)),
                ('username', models.CharField(max_length=30, null=True)),
                ('account_type', models.IntegerField(blank=True, choices=[(1, 'Community'), (2, 'Single'), (3, 'Shadchan')], null=True)),
                ('status', models.IntegerField(choices=[(0, 'Signed Up, Not Completed'), (1, 'Signed Up, Completed'), (2, 'Signed Up Completed, Account Not Verified'), (3, 'Verified'), (4, 'Deactivated by User'), (5, 'Deactivated by Admin')], default=0, help_text='A General status of the users account/account setup')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'ordering': ['date_joined'],
            },
            managers=[
                ('objects', accounts_app.models.CustomUserManger()),
            ],
        ),
        migrations.CreateModel(
            name='Bounty',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('balance', models.PositiveIntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bounty', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('message', models.TextField()),
                ('screenshot', models.ImageField(blank=True, null=True, upload_to='screenshots/')),
                ('status', models.PositiveIntegerField(choices=[(0, 'New'), (1, 'In Progress'), (2, 'Resolved')], default=0)),
                ('subject', models.CharField(blank=True, choices=[('General', 'General'), ('Technical', 'Technical'), ('Billing', 'Billing'), ('Other', 'Other')], max_length=255, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('first_name', models.CharField(blank=True, max_length=40, null=True)),
                ('last_name', models.CharField(blank=True, max_length=40, null=True)),
                ('mothers_first_name', models.CharField(blank=True, max_length=40, null=True)),
                ('mothers_last_name', models.CharField(blank=True, max_length=40, null=True)),
                ('fathers_first_name', models.CharField(blank=True, max_length=40, null=True)),
                ('fathers_last_name', models.CharField(blank=True, max_length=40, null=True)),
                ('gender', models.CharField(blank=True, choices=[('1', 'Male'), ('2', 'Female')], max_length=1, null=True)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('city', models.CharField(blank=True, max_length=25, null=True)),
                ('state', models.CharField(blank=True, max_length=25, null=True)),
                ('phone_number', models.CharField(max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('language', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('English', 'English'), ('Hebrew', 'Hebrew'), ('Yiddish', 'Yiddish'), ('Portuguese', 'Portuguese'), ('Spanish', 'Spanish'), ('French', 'French'), ('Italian', 'Italian'), ('Russian', 'Russian'), ('Ukrainian', 'Ukrainian'), ('German', 'German'), ('Dutch', 'Dutch'), ('Chinese', 'Chinese'), ('Japanese', 'Japanese'), ('Korean', 'Korean'), ('Arabic', 'Arabic'), ('Other', 'Other')], max_length=40), blank=True, default=list, size=None)),
                ('address', models.CharField(blank=True, max_length=40, null=True)),
                ('zip', models.CharField(blank=True, max_length=15, null=True)),
                ('address_confirmed', models.BooleanField(default=False)),
                ('height', models.PositiveIntegerField(blank=True, null=True)),
                ('about', models.TextField(blank=True, help_text='A short description about yourself (keep it meaningful and to the point), 3 to 5 sentences', max_length=500)),
                ('image', models.ImageField(blank=True, storage=project.storage_backends.PrivateMediaStorage(), upload_to='users/images')),
                ('profile_document', models.FileField(blank=True, storage=project.storage_backends.PrivateMediaStorage(), upload_to='users/profile_documents')),
                ('allow_public_profile_download', models.BooleanField(default=False)),
                ('sect', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('Lubavitch', 'Lubavitch'), ('Litvish', 'Litvish'), ('Sefardi', 'Sefardi'), ('Yeshivish', 'Yeshivish'), ('Chassidish', 'Chassidish'), ('Bobov', 'Bobov'), ('Ger', 'Ger'), ('Belz', 'Belz'), ('Breslov', 'Breslov'), ('rachmastrivka', 'rachmastrivka'), ('Satmar', 'Satmar'), ('Skver', 'Skver'), ('Viznitz', 'Viznitz'), ('Modern Orthodox', 'Modern Orthodox'), ('Conservative', 'Conservative'), ('Other', 'Other')], max_length=50), blank=True, default=list, size=None)),
                ('occupation_1', models.CharField(blank=True, max_length=100)),
                ('occupation_2', models.CharField(blank=True, max_length=100)),
                ('shlichus', models.BooleanField(blank=True, null=True)),
                ('shlichus_type', models.PositiveIntegerField(blank=True, choices=[(1, 'Community'), (3, 'OnCampus'), (2, 'Education')], null=True)),
                ('skirt_length', models.PositiveIntegerField(blank=True, choices=[(1, 'Above the knee'), (2, 'On the knee'), (3, 'Below the Knee')], null=True)),
                ('aspirations', models.PositiveIntegerField(blank=True, choices=[(1, 'successful employee'), (2, 'successful business owner'), (3, 'stay at home mom')], null=True)),
                ('education', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, choices=[('Oholei Torah', 'Oholei Torah'), ('United Lubavitcher Yeshiva', 'United Lubavitcher Yeshiva'), ('Coral Springs Yeshiva', 'Coral Springs Yeshiva'), ('LA Yeshiva', 'LA Yeshiva'), ('Chovevei Torah', 'Chovevei Torah'), ('JETS', 'JETS'), ('Wilkes Barre', 'Wilkes Barre'), ('Bonos Menachem', 'Bonos Menachem'), ('Bais Rivka', 'Bais Rivka'), ('Bais Chaya Mushka', 'Bais Chaya Mushka'), ('Bais Chana', 'Bais Chana'), ('Bnos Chomesh', 'Bnos Chomesh'), ('Bnos Menachem', 'Bnos Menachem'), ('Bnos Rabbeinu', 'Bnos Rabbeinu'), ('Bnos Sarah', 'Bnos Sarah')], max_length=50), blank=True, null=True, size=5)),
                ('dor_yeshorim_number', models.CharField(blank=True, max_length=9, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('status', models.PositiveIntegerField(choices=[(0, 'Incomplete'), (1, 'Complete'), (2, 'Not Verified'), (3, 'Verified'), (4, 'Engaged'), (5, 'Married')], default=0)),
                ('site_note', models.TextField(blank=True, help_text='Note for internal use only', max_length=250, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReportSinglesProfile',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reason', models.TextField(max_length=250)),
                ('resolved', models.BooleanField(default=False)),
                ('is_valid', models.BooleanField(default=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_singles_profile', to='accounts_app.profile')),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_singles_profile_reporter', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShadchanProfile',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('secssesfuly_matches', models.PositiveIntegerField(default=0)),
                ('title', models.IntegerField(blank=True, choices=[(1, 'Rabbi'), (2, 'Rebbetzin'), (3, 'Mrs'), (4, 'Mr'), (5, 'Dr')], default=None, help_text='The title of the shadchan', null=True)),
                ('bio', models.TextField(blank=True, help_text='The bio of the shadchan', max_length=500, null=True)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('language', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('English', 'English'), ('Hebrew', 'Hebrew'), ('Yiddish', 'Yiddish'), ('Portuguese', 'Portuguese'), ('Spanish', 'Spanish'), ('French', 'French'), ('Italian', 'Italian'), ('Russian', 'Russian'), ('Ukrainian', 'Ukrainian'), ('German', 'German'), ('Dutch', 'Dutch'), ('Chinese', 'Chinese'), ('Japanese', 'Japanese'), ('Korean', 'Korean'), ('Arabic', 'Arabic'), ('Other', 'Other')], max_length=40), blank=True, default=list, size=None)),
                ('sect', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('Lubavitch', 'Lubavitch'), ('Litvish', 'Litvish'), ('Sefardi', 'Sefardi'), ('Yeshivish', 'Yeshivish'), ('Chassidish', 'Chassidish'), ('Bobov', 'Bobov'), ('Ger', 'Ger'), ('Belz', 'Belz'), ('Breslov', 'Breslov'), ('rachmastrivka', 'rachmastrivka'), ('Satmar', 'Satmar'), ('Skver', 'Skver'), ('Viznitz', 'Viznitz'), ('Modern Orthodox', 'Modern Orthodox'), ('Conservative', 'Conservative'), ('Other', 'Other')], max_length=50), blank=True, default=list, size=None)),
                ('highlights', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, default=list, size=None)),
                ('people_reaching_out', models.PositiveIntegerField(default=0, help_text='The number of people reaching out to the shadchan for help')),
                ('activity_rating', models.PositiveIntegerField(choices=[(0, 'Not Active'), (1, 'Low Activity'), (2, 'Active'), (3, 'Very Active'), (4, 'Extremely Active')], default=0, help_text='The activity rating of the shadchan')),
                ('public_email', models.EmailField(blank=True, help_text='The public email of the shadchan', max_length=254, null=True)),
                ('public_phone_number', models.CharField(blank=True, help_text='The public phone number of the shadchan', null=True)),
                ('profile_image', models.ImageField(blank=True, null=True, storage=project.storage_backends.PrivateMediaStorage(), upload_to='users/images')),
                ('is_active', models.BooleanField(default=True)),
                ('status', models.PositiveIntegerField(choices=[(0, 'Incomplete'), (1, 'Complete'), (2, 'Not Verified'), (3, 'Verified')], default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shadchan_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShadchanGuidelines',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('guideline', models.TextField()),
                ('is_valid', models.BooleanField(default=True)),
                ('shadchan', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shadchan_guidelines', to='accounts_app.shadchanprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShadchanFAQ',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question', models.CharField(max_length=200)),
                ('answer', models.TextField()),
                ('is_valid', models.BooleanField(default=True)),
                ('shadchan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shadchan_faq', to='accounts_app.shadchanprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShadchanReviews',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('review', models.TextField(max_length=500)),
                ('is_valid', models.BooleanField(default=True)),
                ('rating', models.PositiveIntegerField(help_text='The rating of the shadchan from 1 to 5')),
                ('shadchan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shadchan_reviews', to='accounts_app.shadchanprofile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shadchan_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BountyTransaction',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('from_user_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('amount', models.PositiveIntegerField()),
                ('invoice_id', models.CharField(blank=True, help_text='The stripe invoice id that is returned after a payment', max_length=255, null=True, unique=True)),
                ('note', models.CharField(blank=True, max_length=100, null=True)),
                ('is_valid', models.BooleanField(default=True)),
                ('from_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bounty_transaction_from_user', to=settings.AUTH_USER_MODEL)),
                ('to_shadchan', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bounty_transaction_to_shadchan', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bounty_transaction_to_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('from_user__isnull', False), ('from_user_email__isnull', False), _connector='OR'), name='either_from_user_or_from_user_email')],
            },
        ),
    ]
