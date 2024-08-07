# Generated by Django 5.0.7 on 2024-07-28 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluator', '0003_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='correction',
            name='late_submitted_days',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='courseinstance',
            name='allow_late_submission',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='courseinstance',
            name='late_submission_penalty',
            field=models.DecimalField(decimal_places=3, default=None, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='courseinstance',
            name='point_step_size',
            field=models.DecimalField(decimal_places=3, default=1, max_digits=6),
        ),
    ]
