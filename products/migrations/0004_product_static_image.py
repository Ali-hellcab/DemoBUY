from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_order_is_demo_payment_order_payment_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="static_image",
            field=models.CharField(
                blank=True,
                help_text="Path under static/, e.g. images/products/phone.jpg",
                max_length=255,
            ),
        ),
    ]
