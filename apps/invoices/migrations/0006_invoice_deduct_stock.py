# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0005_alter_invoice_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='deduct_stock',
            field=models.BooleanField(default=True, help_text='آیا از موجودی انبار کم شود؟', verbose_name='کم شدن از انبار'),
        ),
    ]
