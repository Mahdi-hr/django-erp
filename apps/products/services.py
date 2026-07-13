from decimal import Decimal


def calculate_product_cost(product):
    from apps.common.models import Setting
    from apps.settings_app.models import FixedCost

    material_cost = Decimal('0')
    for pm in product.materials.all():
        material_cost += pm.quantity * pm.material.purchase_price

    monthly_fixed = Decimal('0')
    for fc in FixedCost.objects.filter(is_active=True):
        monthly_fixed += fc.amount

    water_cost = Decimal(Setting.get_value('water_cost', '0'))
    electricity_cost = Decimal(Setting.get_value('electricity_cost', '0'))
    gas_cost = Decimal(Setting.get_value('gas_cost', '0'))
    service_cost = water_cost + electricity_cost + gas_cost

    cost_price = material_cost + monthly_fixed + service_cost
    product.cost_price = int(cost_price)
    product.save(update_fields=['cost_price'])
    product.recalculate_prices()
    return cost_price


def recalculate_all_products():
    from apps.products.models import Product
    from apps.common.models import Setting

    # Cascade default_profit_percent to all products
    default_profit = Decimal(Setting.get_value('default_profit_percent', '30'))
    Product.objects.filter(is_active=True).update(profit_percent=default_profit)

    for product in Product.objects.filter(is_active=True):
        calculate_product_cost(product)
