# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-09-11 07:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import lessons.filefield


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0004_flashcard_is_bordered'),
    ]

    operations = [
        migrations.CreateModel(
            name='TargetLanguage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_language', models.CharField(max_length=128)),
                ('color', models.CharField(choices=[('RE', 'Red'), ('BL', 'Blue')], default='RE', max_length=32)),
                ('notes', models.CharField(max_length=64)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lessons.Lesson')),
            ],
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_portion_type',
            field=models.CharField(choices=[('GE', 'Generic/Other'), ('GR', 'Greeting'), ('WA', 'Warmup'), ('PE', 'Presentation'), ('PA', 'Practice'), ('PO', 'Production'), ('CO', 'Cooldown'), ('AS', 'Assessment')], default=None, max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_skill_type',
            field=models.CharField(choices=[('VO', 'Vocabulary Practice'), ('CO', 'Speaking Practice'), ('LI', 'Listening Practice'), ('OT', 'Other Skills (e.g.: song, dance)')], default='VO', max_length=32),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_source_type',
            field=models.CharField(choices=[('BF', "Book-Free Activities -- These don't require the book."), ('BB', 'Book-Bound Activities -- These require the book.')], default='BF', max_length=32),
        ),
        migrations.AlterField(
            model_name='course',
            name='course_code',
            field=models.CharField(max_length=12),
        ),
        migrations.AlterField(
            model_name='flashcard',
            name='flashcard_type',
            field=models.CharField(choices=[('PL', 'Flashcard with picture and label'), ('PO', 'Flashcard with picture only'), ('FB', 'Two pages: front (picture) and back (label)')], default='PL', max_length=32),
        ),
        migrations.AlterField(
            model_name='flashcard',
            name='orientation',
            field=models.CharField(choices=[('PO', 'Portrait'), ('LA', 'Landscape')], default='PO', max_length=32),
        ),
        migrations.AlterField(
            model_name='flashcard',
            name='picture',
            field=lessons.filefield.ContentTypeRestrictedFileField(upload_to='media/flashcards/'),
        ),
    ]