import random
import jdatetime
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'ساخت تمام داده‌های تستی سیستم'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n  ===== ساخت داده‌های تستی =====\n'))

        self._create_users()
        self._create_material_categories()
        self._create_materials()
        self._create_products()
        self._create_product_materials()
        self._create_customers()
        self._create_workers()
        self._create_product_inventories()
        self._create_invoices()
        self._create_production_orders()
        self._create_daily_productions()

        self.stdout.write(self.style.SUCCESS('\n  ===== تمام داده‌ها با موفقیت ساخته شد =====\n'))

    def _create_users(self):
        self.stdout.write('  [1/11] ساخت کاربران...')
        users_data = [
            {'username': 'admin', 'full_name': 'مدیر سیستم', 'role': 'admin', 'is_staff': True, 'is_superuser': True},
            {'username': 'accountant', 'full_name': 'احمد حسابدار', 'role': 'accountant'},
            {'username': 'warehouse', 'full_name': 'محمد انباردار', 'role': 'warehouse'},
            {'username': 'operator', 'full_name': 'علی اپراتور', 'role': 'operator'},
            {'username': 'viewer', 'full_name': 'رضا مشاهده‌گر', 'role': 'viewer'},
        ]
        for u in users_data:
            obj, created = User.objects.get_or_create(
                username=u['username'],
                defaults={**u, 'is_active': True}
            )
            if created:
                obj.set_password('admin123')
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'    + {u["full_name"]}'))
            else:
                self.stdout.write(f'    - {u["full_name"]} (وجود دارد)')

    def _create_material_categories(self):
        self.stdout.write('  [2/11] ساخت دسته‌بندی مواد اولیه...')
        from apps.materials.models import MaterialCategory
        cats = [
            ('فلزات', 'ورق، میلگرد، لوله و پروفیل فلزی'),
            ('پلاستیک', 'مواد پلاستیکی و پلیمری'),
            ('رنگ', 'رنگ‌ها و پوشش‌های صنعتی'),
            ('اتصالات', 'پیچ، مهره، پرچ و اتصالات'),
            ('موتور و الکتروموتور', 'موتورهای AC و DC'),
            ('بلبرینگ', 'انواع بلبرینگ و رولبرینگ'),
            ('لاستیک و کاسه‌نمک', 'قطعات لاستیکی و آب‌بندی'),
            ('ابزار', 'ابزارآلات صنعتی'),
        ]
        self._mat_cats = {}
        for name, desc in cats:
            obj, _ = MaterialCategory.objects.get_or_create(name=name, defaults={'description': desc})
            self._mat_cats[name] = obj
        self.stdout.write(self.style.SUCCESS(f'    + {len(cats)} دسته‌بندی'))

    def _create_materials(self):
        self.stdout.write('  [3/11] ساخت 20 ماده اولیه...')
        from apps.materials.models import Material

        units = ['kg', 'piece', 'meter', 'liter', 'roll']
        suppliers = [
            'فولاد مبارکه', 'پتروشیمی بندرامام', 'فولاد خوزستان',
            'شرکت رنگسازی ایران', 'پلیمر پارس', 'اتصالات صنعتی تهران',
            'موتورآذربایجان', 'بلبرینگ اصفهان', 'لاستیک‌سازی تبریز',
            'ابزار دقیق ایران', 'فولاد آلیاژی', 'پتروشیمی شازند',
        ]
        materials_data = [
            ('M001', 'ورق فولادی 3 میلیمتر', 'فلزات', 'kg', 45000, 500),
            ('M002', 'میلگرد 12 میلیمتر', 'فلزات', 'kg', 38000, 800),
            ('M003', 'لوله فولادی 2 اینچ', 'فلزات', 'meter', 120000, 200),
            ('M004', 'پروفیل 40x40', 'فلزات', 'meter', 95000, 300),
            ('M005', 'ورق استیل 1 میلیمتر', 'فلزات', 'kg', 280000, 100),
            ('M006', 'پلی‌اتیلن سنگین', 'پلاستیک', 'kg', 65000, 400),
            ('M007', 'پلی‌پروپیلن', 'پلاستیک', 'kg', 72000, 350),
            ('M008', 'PVC پایپ', 'پلاستیک', 'meter', 35000, 250),
            ('M009', 'رنگ آلکیدی سفید', 'رنگ', 'liter', 180000, 50),
            ('M010', 'رنگ اپوکسی خاکستری', 'رنگ', 'liter', 320000, 30),
            ('M011', 'تینر صنعتی', 'رنگ', 'liter', 45000, 80),
            ('M012', 'پیچ استیل M8', 'اتصالات', 'piece', 2500, 2000),
            ('M013', 'مهره استیل M8', 'اتصالات', 'piece', 1500, 2000),
            ('M014', 'پرچ آلومینیومی', 'اتصالات', 'piece', 800, 5000),
            ('M015', 'موتور 1 اسب بخار', 'موتور و الکتروموتور', 'piece', 3500000, 10),
            ('M016', 'موتور 3 اسب بخار', 'موتور و الکتروموتور', 'piece', 8500000, 5),
            ('M017', 'بلبرینگ 6205', 'بلبرینگ', 'piece', 450000, 20),
            ('M018', 'بلبرینگ 6308', 'بلبرینگ', 'piece', 780000, 15),
            ('M019', 'کاسه‌نمک 50 میلیمتر', 'لاستیک و کاسه‌نمک', 'piece', 120000, 30),
            ('M020', 'اورینگ 40 میلیمتر', 'لاستیک و کاسه‌نمک', 'piece', 25000, 100),
        ]
        self._materials = {}
        for code, name, cat_name, unit, price, stock in materials_data:
            obj, created = Material.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': self._mat_cats[cat_name],
                    'unit': unit,
                    'purchase_price': price,
                    'current_stock': stock,
                    'min_stock': stock // 5,
                    'supplier': random.choice(suppliers),
                    'is_active': True,
                }
            )
            self._materials[code] = obj
            if created:
                self.stdout.write(self.style.SUCCESS(f'    + {name}'))
        self.stdout.write(self.style.SUCCESS(f'    مجموع: {len(self._materials)} ماده اولیه'))

    def _create_products(self):
        self.stdout.write('  [4/11] ساخت 20 محصول...')
        from apps.products.models import Product

        categories = ['در و پنجره', 'نرده و حفاظ', 'استخر و آب‌بندی', 'تجهیزات صنعتی', 'لوازم خانگی']
        products_data = [
            ('P001', 'پنجره UPVC دو لنگه', 'در و پنجره', 28000000, 18000000),
            ('P002', 'پنجره UPVC تک لنگه', 'در و پنجره', 18000000, 12000000),
            ('P003', 'درب ضد سرقت', 'در و پنجره', 45000000, 30000000),
            ('P004', 'درب داخلی HDF', 'در و پنجره', 12000000, 8000000),
            ('P005', 'نرده استیل راه پله', 'نرده و حفاظ', 3500000, 2200000),
            ('P006', 'نرده آلومینیومی بالکن', 'نرده و حفاظ', 4200000, 2800000),
            ('P007', 'حفاظ شاخ گوزنی', 'نرده و حفاظ', 2800000, 1800000),
            ('P008', 'حفاظ پنجره ساده', 'نرده و حفاظ', 1500000, 900000),
            ('P009', 'وان فایبرگلاس', 'استخر و آب‌بندی', 15000000, 9500000),
            ('P010', 'جکوزی خانگی', 'استخر و آب‌بندی', 35000000, 22000000),
            ('P011', 'کانال گالوانیزه', 'تجهیزات صنعتی', 850000, 550000),
            ('P012', 'دریچه کولر', 'تجهیزات صنعتی', 650000, 420000),
            ('P013', 'شیر فلکچه 1 اینچ', 'تجهیزات صنعتی', 4200000, 2800000),
            ('P014', 'پمپ آب خانگی', 'تجهیزات صنعتی', 6800000, 4500000),
            ('P015', 'بخاری برقی فن‌دار', 'لوازم خانگی', 3200000, 2100000),
            ('P016', 'هیتر برقی صنعتی', 'لوازم خانگی', 8500000, 5500000),
            ('P017', 'روفتایل سفالی', 'لوازم خانگی', 45000, 28000),
            ('P018', 'ورق سینوسی رنگی', 'لوازم خانگی', 120000, 75000),
            ('P019', 'دیگ بخار صنعتی', 'تجهیزات صنعتی', 25000000, 16000000),
            ('P020', 'مخزن آب پلی‌اتیلن', 'تجهیزات صنعتی', 4500000, 2800000),
        ]
        self._products = {}
        for code, name, cat, sale, cost in products_data:
            profit = round((sale - cost) / cost * 100, 1)
            obj, created = Product.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': cat,
                    'sale_price': sale,
                    'wholesale_price': int(sale * 0.85),
                    'retail_price': int(sale * 1.1),
                    'cost_price': cost,
                    'profit_percent': profit,
                    'is_active': True,
                }
            )
            self._products[code] = obj
            if created:
                self.stdout.write(self.style.SUCCESS(f'    + {name}'))
        self.stdout.write(self.style.SUCCESS(f'    مجموع: {len(self._products)} محصول'))

    def _create_product_materials(self):
        self.stdout.write('  [5/11] ساخت لیست مواد مصرفی محصولات...')
        from apps.products.models import ProductMaterial

        links = [
            ('P001', 'M001', 12, 'kg'),
            ('P001', 'M008', 4, 'meter'),
            ('P001', 'M012', 8, 'piece'),
            ('P002', 'M001', 8, 'kg'),
            ('P002', 'M008', 3, 'meter'),
            ('P003', 'M001', 25, 'kg'),
            ('P003', 'M017', 2, 'piece'),
            ('P003', 'M009', 2, 'liter'),
            ('P004', 'M006', 5, 'kg'),
            ('P005', 'M005', 3, 'kg'),
            ('P005', 'M012', 6, 'piece'),
            ('P006', 'M004', 2, 'meter'),
            ('P007', 'M002', 8, 'kg'),
            ('P008', 'M002', 4, 'kg'),
            ('P009', 'M006', 15, 'kg'),
            ('P010', 'M006', 25, 'kg'),
            ('P010', 'M015', 1, 'piece'),
            ('P011', 'M001', 3, 'kg'),
            ('P013', 'M005', 2, 'kg'),
            ('P014', 'M015', 1, 'piece'),
            ('P014', 'M019', 2, 'piece'),
            ('P015', 'M016', 1, 'piece'),
            ('P019', 'M001', 40, 'kg'),
            ('P020', 'M006', 20, 'kg'),
        ]
        count = 0
        for prod_code, mat_code, qty, unit in links:
            if prod_code in self._products and mat_code in self._materials:
                _, created = ProductMaterial.objects.get_or_create(
                    product=self._products[prod_code],
                    material=self._materials[mat_code],
                    defaults={'quantity': Decimal(str(qty)), 'unit': unit}
                )
                if created:
                    count += 1
        self.stdout.write(self.style.SUCCESS(f'    + {count} اتصال محصول-ماده'))

    def _create_customers(self):
        self.stdout.write('  [6/11] ساخت 15 مشتری...')
        from apps.customers.models import Customer

        cities = ['تهران', 'اصفهان', 'شیراز', 'تبریز', 'مشهد', 'اهواز', 'کرمان', 'یزد']
        companies = [
            'شرکت ساختمانی پارس', 'گروه صنعتی آهن', 'شرکت تأسیساتی نوین',
            'پیمانکاری عمران', 'شرکت بازرگانی جهان', 'گروه مهندسی پردیس',
            'شرکت تجهیزاتی صنعتی', 'بازرگانی بین‌المللی نور',
            'شرکت ساختمانی آریا', 'گروه صنعتی کیان', 'شرکت پتروشیمی جنوب',
            'مصالح ساختمانی البرز', 'تأمین تجهیزات صنعت', 'شرکت استخرسازی آبی',
            'دکوراسیون مدرن',
        ]
        first_names = ['محمد', 'علی', 'رضا', 'احمد', 'حسن', 'حسین', 'امیر', 'عباس', ' maryam', 'فاطمه', 'سارا', 'نیلوفر', 'زهرا', 'مریم', 'النا']
        last_names = ['احمدی', 'محمدی', 'رضایی', 'کریمی', '彈مرادی', 'حیدری', 'نجفی', 'رحیمی', 'مقیمی', 'طلوعی', 'src', 'sha', 'gha', 'moh', 'ali']

        self._customers = []
        for i in range(15):
            name = f'{first_names[i]} {last_names[i]}'
            phone = f'091{random.randint(10000000, 99999999)}'
            obj, created = Customer.objects.get_or_create(
                phone=phone,
                defaults={
                    'name': name,
                    'company': companies[i],
                    'email': f'{first_names[i]}@example.com',
                    'address': f'خیابان {random.choice(["آزادی", "انقلاب", "ولیعصر", "هفت‌تیر", "نبرد"])} پلاک {random.randint(10, 200)}',
                    'city': random.choice(cities),
                    'balance': random.randint(0, 50000000),
                    'credit_limit': random.choice([100000000, 200000000, 500000000]),
                    'discount_percent': random.choice([0, 5, 10, 15]),
                    'is_active': True,
                }
            )
            self._customers.append(obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f'    + {name} ({companies[i]})'))
        self.stdout.write(self.style.SUCCESS(f'    مجموع: {len(self._customers)} مشتری'))

    def _create_workers(self):
        self.stdout.write('  [7/11] ساخت 5 کارگر...')
        from apps.workers.models import Worker

        workers_data = [
            ('علی رضایی', '09121234567', 'welder', 'جوشکار CO2 و آرگون', 8, 18000000),
            ('محمد حسینی', '09132345678', 'assembler', 'مونتاژ در و پنجره', 5, 15000000),
            ('رضا کریمی', '09143456789', 'painter', 'رنگ‌کاری صنعتی', 12, 20000000),
            ('احمد نجفی', '09154567890', 'operator', 'اپراتور CNC', 3, 14000000),
            ('حسن مرادی', '09165678901', 'packer', 'بسته‌بندی و بارگیری', 2, 12000000),
        ]
        self._workers = []
        for name, phone, role, skill, exp, salary in workers_data:
            obj, created = Worker.objects.get_or_create(
                name=name,
                defaults={
                    'phone': phone,
                    'role': role,
                    'skill': skill,
                    'experience_years': exp,
                    'salary': salary,
                    'national_id': f'{random.randint(1000000000, 9999999999)}',
                    'address': f'تهران، خیابان {random.choice(["آزادی", "انقلاب", " ولیعصر"])}',
                    'birth_date': date(random.randint(1355, 1375), random.randint(1, 12), random.randint(1, 28)),
                    'hire_date': date(random.randint(1395, 1402), random.randint(1, 12), random.randint(1, 28)),
                    'is_active': True,
                }
            )
            self._workers.append(obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f'    + {name} ({skill})'))
        self.stdout.write(self.style.SUCCESS(f'    مجموع: {len(self._workers)} کارگر'))

    def _create_product_inventories(self):
        self.stdout.write('  [8/11] ساخت موجودی محصولات...')
        from apps.inventory.models import ProductInventory

        count = 0
        for code, prod in self._products.items():
            obj, created = ProductInventory.objects.get_or_create(
                product=prod,
                defaults={
                    'current_stock': random.randint(5, 100),
                    'min_stock': random.randint(2, 10),
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'    + {count} موجودی محصول'))

    def _create_invoices(self):
        self.stdout.write('  [9/11] ساخت 8 فاکتور...')
        from apps.invoices.models import Invoice, InvoiceItem
        from apps.products.models import Product

        statuses = ['paid', 'paid', 'paid', 'partial', 'partial', 'draft', 'draft', 'sent']
        types = ['sale', 'sale', 'sale', 'sale', 'proforma', 'sale', 'cash', 'official']
        admin = User.objects.filter(role='admin').first()

        for i in range(8):
            customer = random.choice(self._customers)
            inv_type = types[i]
            status = statuses[i]
            issue = date.today() - timedelta(days=random.randint(0, 30))

            inv, created = Invoice.objects.get_or_create(
                invoice_number=f'INV-1404-{i+1:04d}',
                defaults={
                    'customer': customer,
                    'type': inv_type,
                    'status': status,
                    'issue_date': issue,
                    'discount_amount': random.choice([0, 500000, 1000000, 2000000]),
                    'payment_method': random.choice(['نقدی', 'چکی', 'کارت به کارت', 'transfer', '']),
                    'notes': random.choice(['', 'ارسال فوری', 'تحویل درب کارخانه', 'شماره تماس: ۰۲۱-۱۲۳۴۵۶۷۸']),
                    'deduct_stock': True,
                    'created_by': admin,
                }
            )
            if not created:
                continue

            # اقلام فاکتور
            num_items = random.randint(1, 4)
            chosen_products = random.sample(list(self._products.values()), min(num_items, len(self._products)))
            subtotal = 0
            for prod in chosen_products:
                qty = random.randint(1, 10)
                price = prod.sale_price
                disc = random.choice([0, 5, 10])
                item_total = int(qty * price * (1 - disc / 100))
                InvoiceItem.objects.create(
                    invoice=inv,
                    product=prod,
                    description=prod.name,
                    quantity=qty,
                    unit_price=price,
                    discount_percent=disc,
                    tax_percent=10,
                    total=item_total,
                )
                subtotal += item_total

            inv.subtotal = subtotal
            inv.tax_amount = int(subtotal * 0.1)
            inv.total = subtotal + inv.tax_amount - inv.discount_amount
            if status == 'paid':
                inv.paid_amount = inv.total
            elif status == 'partial':
                inv.paid_amount = int(inv.total * random.uniform(0.3, 0.7))
            else:
                inv.paid_amount = 0
            inv.remaining_amount = inv.total - inv.paid_amount
            inv.save()

            self.stdout.write(self.style.SUCCESS(f'    + فاکتور {inv.invoice_number} - {customer.name} - {inv.total:,} ریال ({status})'))

    def _create_production_orders(self):
        self.stdout.write('  [10/11] ساخت 5 سفارش تولید...')
        from apps.production.models import ProductionOrder, ProductionMaterial

        statuses = ['completed', 'completed', 'in_progress', 'pending', 'pending']
        priorities = [1, 2, 3, 4, 5]
        admin = User.objects.filter(role='admin').first()

        for i in range(5):
            prod = random.choice(list(self._products.values()))
            qty = random.randint(10, 100)
            status = statuses[i]
            planned = date.today() - timedelta(days=random.randint(0, 20))

            order, created = ProductionOrder.objects.get_or_create(
                product=prod,
                quantity=qty,
                defaults={
                    'status': status,
                    'priority': priorities[i],
                    'planned_date': planned,
                    'start_date': planned if status in ['in_progress', 'completed'] else None,
                    'end_date': (planned + timedelta(days=random.randint(3, 10))) if status == 'completed' else None,
                    'notes': random.choice(['', 'اولویت بالا', 'مشتری VIP', 'تولید فوری']),
                    'created_by': admin,
                }
            )
            if created:
                order.calculate_costs()

                # مواد مصرفی
                for pm in prod.materials.all():
                    ProductionMaterial.objects.get_or_create(
                        order=order,
                        material=pm.material,
                        defaults={
                            'planned_quantity': pm.quantity * qty,
                            'actual_quantity': (pm.quantity * Decimal(str(qty)) * Decimal(str(round(random.uniform(0.95, 1.05), 2)))) if status == 'completed' else None,
                        }
                    )
                self.stdout.write(self.style.SUCCESS(f'    + سفارش #{order.pk} - {prod.name} x {qty} ({status})'))

    def _create_daily_productions(self):
        self.stdout.write('  [11/11] ساخت 10 تولید روزانه...')
        from apps.production.models import DailyProduction

        admin = User.objects.filter(role='admin').first()
        statuses = ['completed'] * 7 + ['pending'] * 3

        for i in range(10):
            worker = random.choice(self._workers)
            prod = random.choice(list(self._products.values()))
            qty = random.randint(5, 50)
            prod_date = date.today() - timedelta(days=random.randint(0, 14))
            status = statuses[i]

            obj, created = DailyProduction.objects.get_or_create(
                worker=worker,
                product=prod,
                production_date=prod_date,
                quantity=qty,
                defaults={
                    'status': status,
                    'notes': random.choice(['', 'تولید خوب', 'کیفیت عالی', 'نیاز به بازرسی']),
                    'created_by': admin,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'    + {worker.name} - {prod.name} x {qty} ({prod_date})'))
