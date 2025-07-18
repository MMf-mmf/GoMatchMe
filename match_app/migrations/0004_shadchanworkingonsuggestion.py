# Generated by Django 5.1.2 on 2025-03-12 15:21

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_app', '0002_alter_profile_sect_alter_shadchanprofile_sect'),
        ('match_app', '0003_suggestion_status_alter_suggestion_boys_sect_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShadchanWorkingOnSuggestion',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('shadchan', models.ForeignKey(help_text='The shadchan that is working on the suggestion', on_delete=django.db.models.deletion.CASCADE, related_name='suggestions_working_on', to='accounts_app.shadchanprofile')),
                ('suggestion', models.ForeignKey(help_text='The suggestion that the shadchan is working on', on_delete=django.db.models.deletion.CASCADE, related_name='shadchanim_working_on', to='match_app.suggestion')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
