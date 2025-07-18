# Generated by Django 5.1.2 on 2024-11-01 01:30

import django.db.models.deletion
import django_countries.fields
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Suggestion',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('message', models.TextField(blank=True, help_text='The message that the user wrote when making the suggestion', null=True)),
                ('email', models.EmailField(blank=True, help_text='The email of the user that made the suggestion, if the user was not logged in', max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, help_text='The phone of the user that made the suggestion, if the user was not logged in', max_length=30, null=True)),
                ('boys_first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('boys_last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('boys_mothers_name', models.CharField(blank=True, max_length=50, null=True)),
                ('boys_fathers_name', models.CharField(blank=True, max_length=50, null=True)),
                ('boys_age', models.PositiveIntegerField(blank=True, null=True)),
                ('boys_country', django_countries.fields.CountryField(max_length=2)),
                ('boys_city', models.CharField(blank=True, max_length=50, null=True)),
                ('girls_first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('girls_last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('girls_mothers_name', models.CharField(blank=True, max_length=50, null=True)),
                ('girls_fathers_name', models.CharField(blank=True, max_length=50, null=True)),
                ('girls_age', models.PositiveIntegerField(blank=True, null=True)),
                ('girls_country', django_countries.fields.CountryField(max_length=2)),
                ('girls_city', models.CharField(blank=True, max_length=50, null=True)),
                ('amount', models.PositiveIntegerField(blank=True, null=True)),
                ('ranking', models.PositiveIntegerField(choices=[(1, 'Copper'), (2, 'Silver'), (3, 'Gold'), (4, 'Platinum'), (5, 'Platinum Plus')], default=1, help_text='how we rank how good the suggestion is')),
                ('is_active', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('stripe_checkout_session_id', models.CharField(blank=True, max_length=255, null=True)),
                ('stripe_invoice_id', models.CharField(blank=True, max_length=255, null=True)),
                ('strikes', models.PositiveIntegerField(default=0, help_text='how many times the suggestion has been reported')),
                ('for_boy', models.ForeignKey(blank=True, help_text='The user that the suggestion was made for', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suggestions_received_for_boy', to=settings.AUTH_USER_MODEL)),
                ('for_girl', models.ForeignKey(blank=True, help_text='The user that the suggestion was made for', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suggestions_received_for_girl', to=settings.AUTH_USER_MODEL)),
                ('made_by', models.ForeignKey(blank=True, help_text='The user that made the suggestion', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suggestions_made', to=settings.AUTH_USER_MODEL)),
                ('tagged_users', models.ManyToManyField(blank=True, help_text='The Shadchonim that are tagged in the suggestion', related_name='tagged_suggestions', to=settings.AUTH_USER_MODEL)),
                ('views', models.ManyToManyField(blank=True, related_name='suggestions_viewed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='ReportSuggestion',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('message', models.TextField(help_text='The message that the reporter wrote when reporting the suggestion')),
                ('reporter', models.ForeignKey(help_text='The user that is reporting the suggestion', on_delete=django.db.models.deletion.CASCADE, related_name='reported_suggestions', to='accounts_app.shadchanprofile')),
                ('suggestion', models.ForeignKey(help_text='The suggestion that is being reported', on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='match_app.suggestion')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
