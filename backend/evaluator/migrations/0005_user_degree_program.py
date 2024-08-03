# Generated by Django 5.0.7 on 2024-08-01 11:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluator', '0004_late_submission'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDegreeProgram',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('degree_program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='udp_degree_program', to='evaluator.degreeprogram')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='udp_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'degree_program')},
            },
        ),
    ]