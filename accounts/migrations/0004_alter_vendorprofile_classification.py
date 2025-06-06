# Generated by Django 5.2 on 2025-05-15 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_vendorprofile_classification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorprofile',
            name='classification',
            field=models.CharField(choices=[('bronze', 'Bronze (20%)'), ('silver', 'Silver (15%)'), ('gold', 'Gold (10%)'), ('platinum', 'Platinum (5%)'), ('special', 'Special (Custom)')], default='bronze', max_length=20),
        ),
    ]
