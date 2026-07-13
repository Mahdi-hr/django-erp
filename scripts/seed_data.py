"""
Seed script - imports all data from دیتا.txt into the Django database.
Run: python scripts/seed_data.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings')
django.setup()

from django.db import transaction
from decimal import Decimal


def seed_users():
    from apps.users.models import User
    users_data = [
        ('admin', 'admin123', 'مدیر سیستم', 'admin', 'admin@factory.com'),
        ('accountant', 'admin123', 'حسابدار', 'accountant', 'accountant@factory.com'),
        ('warehouse', 'admin123', 'انباردار', 'warehouse', 'warehouse@factory.com'),
        ('operator', 'admin123', 'اپراتور تولید', 'operator', 'operator@factory.com'),
    ]
    created = 0
    for uname, pwd, fname, role, email in users_data:
        if not User.objects.filter(username=uname).exists():
            u = User.objects.create_user(
                username=uname, password=pwd,
                full_name=fname, role=role, email=email
            )
            created += 1
    print(f'  Users: {created} created')


def seed_settings():
    from apps.common.models import Setting
    settings_data = [
        ('company_name', 'کارخانه تجهیزات فلزی و گازی', 'general', 'نام کارخانه'),
        ('company_phone', '021-12345678', 'general', 'تلفن تماس'),
        ('company_address', '', 'general', 'آدرس کارخانه'),
        ('company_logo', '', 'general', 'لوگوی کارخانه'),
        ('currency', 'IRR', 'financial', 'واحد پول'),
        ('tax_rate', '9', 'financial', 'درصد مالیات'),
        ('default_profit_percent', '30', 'financial', 'درصد سود پیش‌فرض'),
        ('insurance_cost', '500000', 'financial', 'هزینه بیمه ماهانه'),
        ('transport_cost', '300000', 'financial', 'هزینه حمل و نقل ماهانه'),
        ('depreciation_cost', '200000', 'financial', 'هزینه استهلاک ماهانه'),
        ('low_stock_threshold', '10', 'inventory', 'آستانه هشدار کمبود'),
        ('out_of_stock_threshold', '0', 'inventory', 'آستانه اتمام کالا'),
        ('water_cost', '0', 'production', 'هزینه آب ماهانه'),
        ('electricity_cost', '0', 'production', 'هزینه برق ماهانه'),
        ('gas_cost', '0', 'production', 'هزینه گاز ماهانه'),
        ('wholesale_multiplier', '0.85', 'financial', 'ضریب قیمت عمده'),
        ('retail_multiplier', '1.1', 'financial', 'ضریب قیمت جزئی'),
        ('dealer_multiplier', '0.90', 'financial', 'ضریب قیمت نمایندگی'),
        ('export_multiplier', '1.15', 'financial', 'ضریب قیمت صادراتی'),
        ('special_multiplier', '0.80', 'financial', 'ضریب قیمت ویژه'),
    ]
    created = 0
    for key, val, cat, desc in settings_data:
        _, was_created = Setting.objects.update_or_create(
            key=key, defaults={'value': val, 'category': cat, 'description': desc}
        )
        if was_created:
            created += 1
    print(f'  Settings: {created} created')


def seed_material_categories():
    from apps.materials.models import MaterialCategory
    cats = [
        (1, 'فلزات', 'مواد فلزی و پروفیل‌ها', 1),
        (2, 'رنگ', 'رنگ‌های صنعتی', 2),
        (3, 'شیرآلات', 'شیرهای گازی و فلکه‌ای', 3),
        (4, 'اتصالات', 'مهره‌ها، پیچ‌ها و واشرها', 4),
        (5, 'سایر', 'سایر مواد مصرفی', 5),
        (6, 'هزینه جوش', 'هزینه‌های جوشکاری بر اساس سایز', 6),
    ]
    created = 0
    for cid, name, desc, order in cats:
        _, was_created = MaterialCategory.objects.update_or_create(
            id=cid, defaults={'name': name, 'description': desc, 'sort_order': order}
        )
        if was_created:
            created += 1
    print(f'  Material Categories: {created} created')


def seed_materials():
    from apps.materials.models import Material, MaterialCategory
    cat_flz = MaterialCategory.objects.get(id=1)
    cat_rng = MaterialCategory.objects.get(id=2)
    cat_shr = MaterialCategory.objects.get(id=3)
    cat_ets = MaterialCategory.objects.get(id=4)
    cat_jws = MaterialCategory.objects.get(id=6)

    materials = [
        # Flz
        ('MAT-001', 'پروفیل', 'kg', 120000, 100, 500, cat_flz),
        ('MAT-002', 'پلیت', 'piece', 50000, 50, 200, cat_flz),
        # Rng
        ('MAT-003', 'رنگ 1', 'kg', 250000, 20, 100, cat_rng),
        ('MAT-004', 'رنگ 2', 'kg', 280000, 20, 80, cat_rng),
        ('MAT-005', 'رنگ 3', 'kg', 300000, 20, 60, cat_rng),
        # Shr
        ('MAT-006', 'شیر دسته گازی', 'piece', 350000, 30, 150, cat_shr),
        ('MAT-007', 'شیر فلکه‌ای', 'piece', 450000, 20, 100, cat_shr),
        # Ets
        ('MAT-008', 'مهره برنجی', 'piece', 15000, 100, 500, cat_ets),
        ('MAT-009', 'مهره آهنی', 'piece', 8000, 100, 600, cat_ets),
        ('MAT-010', 'پیچ 1.3', 'piece', 5000, 200, 1000, cat_ets),
        ('MAT-011', 'پیچ 2.5', 'piece', 8000, 200, 800, cat_ets),
        ('MAT-012', 'پیچ 3.5', 'piece', 12000, 100, 500, cat_ets),
        ('MAT-013', 'پیچ 6', 'piece', 20000, 100, 300, cat_ets),
        ('MAT-014', 'واشر', 'piece', 3000, 200, 1000, cat_ets),
        # Jws
        ('MAT-015', 'هزینه جوش', 'unit', 0, 0, 0, cat_jws),
        ('WELD-001', 'تک شعله 45x45', 'unit', 25000, 0, 0, cat_jws),
        ('WELD-002', 'تک شعله 50x50', 'unit', 30000, 0, 0, cat_jws),
        ('WELD-003', '45x45 ژوپن', 'unit', 35000, 0, 0, cat_jws),
        ('WELD-004', '50x50 ژوپن', 'unit', 40000, 0, 0, cat_jws),
        ('WELD-005', '60x60', 'unit', 45000, 0, 0, cat_jws),
        ('WELD-006', '60x60 ژوپن', 'unit', 50000, 0, 0, cat_jws),
        ('WELD-007', '70x70', 'unit', 55000, 0, 0, cat_jws),
        ('WELD-008', '90x90', 'unit', 70000, 0, 0, cat_jws),
        ('WELD-009', 'دو قلو', 'unit', 80000, 0, 0, cat_jws),
        ('WELD-010', 'سه قلو', 'unit', 100000, 0, 0, cat_jws),
        ('WELD-011', 'دو قلو پایه', 'unit', 90000, 0, 0, cat_jws),
        ('WELD-012', 'سه قلو پایه', 'unit', 120000, 0, 0, cat_jws),
        ('WELD-013', 'تک شعله دور ورق', 'unit', 35000, 0, 0, cat_jws),
        ('WELD-014', '50x50 چدنی', 'unit', 60000, 0, 0, cat_jws),
        ('WELD-015', 'تنور گازی', 'unit', 150000, 0, 0, cat_jws),
    ]
    created = 0
    for code, name, unit, price, min_s, cur_s, cat in materials:
        _, was_created = Material.objects.update_or_create(
            code=code,
            defaults={
                'name': name, 'unit': unit, 'purchase_price': price,
                'min_stock': min_s, 'current_stock': cur_s, 'category': cat,
            }
        )
        if was_created:
            created += 1
    print(f'  Materials: {created} created')


def seed_fixed_costs():
    from apps.settings_app.models import FixedCost
    costs = [
        ('مزد جوشکار', 15000000, 'labor'),
        ('مزد کارگر کف', 12000000, 'labor'),
        ('بیمه', 500000, 'insurance'),
        ('حمل و نقل', 300000, 'transport'),
        ('استهلاک', 200000, 'depreciation'),
        ('آب', 150000, 'utilities'),
        ('برق', 400000, 'utilities'),
        ('گاز', 200000, 'utilities'),
        ('هزینه بسته‌بندی', 50000, 'packaging'),
        ('هزینه متفرقه', 100000, 'miscellaneous'),
    ]
    created = 0
    for name, amount, cat in costs:
        _, was_created = FixedCost.objects.update_or_create(
            name=name, defaults={'amount': amount, 'category': cat}
        )
        if was_created:
            created += 1
    print(f'  Fixed Costs: {created} created')


def seed_products():
    from apps.products.models import Product, ProductMaterial
    from apps.materials.models import Material

    products_data = [
        ('PRD-001', 'اجاق گاز تک شعله 45x45', 'اجاق گاز', 'اجاق گاز تک شعله سایز 45x45'),
        ('PRD-002', 'اجاق گاز تک شعله 50x50', 'اجاق گاز', 'اجاق گاز تک شعله سایز 50x50'),
        ('PRD-003', 'اجاق گاز دو قلو', 'اجاق گاز', 'اجاق گاز دو قلو'),
        ('PRD-004', 'اجاق گاز سه قلو', 'اجاق گاز', 'اجاق گاز سه قلو'),
        ('PRD-005', 'تنور گازی', 'تنور', 'تنور گازی صنعتی'),
    ]
    created = 0
    for code, name, cat, desc in products_data:
        _, was_created = Product.objects.update_or_create(
            code=code, defaults={'name': name, 'category': cat, 'description': desc}
        )
        if was_created:
            created += 1
    print(f'  Products: {created} created')


def seed_product_materials():
    from apps.products.models import Product, ProductMaterial
    from apps.materials.models import Material

    bom_data = {
        'PRD-001': [
            ('MAT-001', 5, 'kg'),
            ('MAT-003', 0.5, 'kg'),
            ('MAT-006', 1, 'piece'),
            ('MAT-008', 4, 'piece'),
            ('MAT-011', 8, 'piece'),
            ('MAT-014', 8, 'piece'),
            ('MAT-002', 2, 'piece'),
            ('WELD-001', 1, 'unit'),
        ],
        'PRD-002': [
            ('MAT-001', 7, 'kg'),
            ('MAT-004', 0.6, 'kg'),
            ('MAT-006', 1, 'piece'),
            ('MAT-008', 4, 'piece'),
            ('MAT-011', 8, 'piece'),
            ('MAT-014', 8, 'piece'),
            ('MAT-002', 2, 'piece'),
            ('WELD-002', 1, 'unit'),
        ],
        'PRD-003': [
            ('MAT-001', 12, 'kg'),
            ('MAT-003', 1, 'kg'),
            ('MAT-006', 2, 'piece'),
            ('MAT-008', 8, 'piece'),
            ('MAT-011', 16, 'piece'),
            ('MAT-014', 16, 'piece'),
            ('MAT-002', 4, 'piece'),
            ('WELD-009', 1, 'unit'),
        ],
    }
    created = 0
    for prod_code, materials in bom_data.items():
        product = Product.objects.get(code=prod_code)
        for mat_code, qty, unit in materials:
            material = Material.objects.get(code=mat_code)
            _, was_created = ProductMaterial.objects.update_or_create(
                product=product, material=material,
                defaults={'quantity': qty, 'unit': unit}
            )
            if was_created:
                created += 1
    print(f'  Product Materials (BOM): {created} created')


def calculate_all_prices():
    from apps.products.models import Product, ProductMaterial
    from apps.materials.models import Material
    from apps.common.models import Setting

    profit_pct = Decimal(Setting.get_value('default_profit_percent', '30'))
    tax_rate = Decimal(Setting.get_value('tax_rate', '9'))
    wholesale_mult = Decimal(Setting.get_value('wholesale_multiplier', '0.85'))

    fixed_total = Decimal('0')
    from apps.settings_app.models import FixedCost
    for fc in FixedCost.objects.filter(is_active=True):
        if fc.category != 'packaging':
            fixed_total += fc.amount

    products = Product.objects.all()
    updated = 0
    for product in products:
        # Calculate material cost from BOM
        material_cost = Decimal('0')
        for pm in product.materials.all():
            material_cost += pm.quantity * pm.material.purchase_price

        # Total cost = material + fixed
        cost_price = material_cost + fixed_total
        product.cost_price = int(cost_price)

        # Sale price = cost * (1 + profit%) * (1 + tax%)
        product.sale_price = int(cost_price * (1 + profit_pct / 100) * (1 + tax_rate / 100))

        # Wholesale = sale * multiplier
        product.wholesale_price = int(product.sale_price * wholesale_mult)

        # Other prices
        retail_mult = Decimal(Setting.get_value('retail_multiplier', '1.1'))
        dealer_mult = Decimal(Setting.get_value('dealer_multiplier', '0.90'))
        export_mult = Decimal(Setting.get_value('export_multiplier', '1.15'))
        special_mult = Decimal(Setting.get_value('special_multiplier', '0.80'))
        product.retail_price = int(product.sale_price * retail_mult)
        product.dealer_price = int(product.sale_price * dealer_mult)
        product.export_price = int(product.sale_price * export_mult)
        product.special_price = int(product.sale_price * special_mult)

        product.save(update_fields=[
            'cost_price', 'sale_price', 'wholesale_price',
            'retail_price', 'dealer_price', 'export_price', 'special_price'
        ])
        updated += 1
        mat_cost_fmt = f'{material_cost:,.0f}'
        cost_fmt = f'{cost_price:,.0f}'
        sale_fmt = f'{product.sale_price:,.0f}'
        print(f'    {product.name}: mat={mat_cost_fmt} | cost={cost_fmt} | sale={sale_fmt} RIAL')

    print(f'  Prices calculated for {updated} products')


@transaction.atomic
def run():
    print('=' * 50)
    print('  Seeding database from data file')
    print('=' * 50)
    print()

    print('[1/7] Users...')
    seed_users()

    print('[2/7] Settings...')
    seed_settings()

    print('[3/7] Material Categories...')
    seed_material_categories()

    print('[4/7] Materials...')
    seed_materials()

    print('[5/7] Fixed Costs...')
    seed_fixed_costs()

    print('[6/7] Products...')
    seed_products()

    print('[7/7] Product Materials (BOM)...')
    seed_product_materials()

    print()
    print('Calculating prices...')
    calculate_all_prices()

    print()
    print('=' * 50)
    print('  DONE! All data imported successfully.')
    print('=' * 50)


if __name__ == '__main__':
    run()
