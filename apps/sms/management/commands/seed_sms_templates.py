from django.core.management.base import BaseCommand
from apps.sms.models import SMSTemplate


TEMPLATES = [
    {
        'name': 'لیست قیمت',
        'title': 'لیست قیمت محصولات',
        'category': 'general',
        'body': 'با سلام\nلیست قیمت جدید محصولات {company} به شرح زیر است:\n\n{products}\n\nبرای ثبت سفارش با ما در تماس باشید.\nبا تشکر',
    },
    {
        'name': 'ارسال فاکتور',
        'title': 'اطلاع‌رسانی فاکتور',
        'category': 'order',
        'body': 'مشتری گرامی {customer}\nفاکتور شماره {invoice_number} به مبلغ {amount} ریال صادر شد.\nجهت مشاهده فاکتور به پنل کاربری مراجعه کنید.\nبا تشکر',
    },
    {
        'name': 'تایید سفارش',
        'title': 'تایید دریافت سفارش',
        'category': 'order',
        'body': 'مشتری گرامی {customer}\nسفارش شماره {order_number} با موفقیت ثبت شد.\nزمان تقریبی آماده‌سازی: {delivery_time}\nبا تشکر از اعتماد شما',
    },
    {
        'name': 'تخفیف ویژه',
        'title': 'پیشنهاد ویژه برای شما',
        'category': 'discount',
        'body': 'مشتری گرامی {customer}\nویژه شما! تخفیف {discount}% روی تمامی محصولات\nاز {start_date} تا {end_date}\nجهت بهره‌مندی از تخفیف با ما تماس بگیرید.\nبا تشکر',
    },
    {
        'name': 'یادآوری پرداخت',
        'title': 'یادآوری پرداخت بدهی',
        'category': 'payment',
        'body': 'مشتری گرامی {customer}\nمبلغ {amount} ریال بابت فاکتور شماره {invoice_number} معوق است.\nلطفاً نسبت به تسویه حساب اقدام فرمایید.\nبا تشکر',
    },
    {
        'name': 'محصول جدید',
        'title': 'معرفی محصول جدید',
        'category': 'new_product',
        'body': 'مشتری گرامی {customer}\nمحصول جدید {product_name} به مجموعه محصولات اضافه شد!\nقیمت: {price} ریال\nجهت سفارش با ما در تماس باشید.\nبا تشکر',
    },
    {
        'name': 'تبریک تولد',
        'title': 'تبریک تولد مشتری',
        'category': 'birthday',
        'body': 'مشتری گرامی {customer}\nتولد شما مبارک!\nبرای قدردانی از همراهی شما، تخفیف ویژه {discount}% در نظر گرفته شد.\nتخفیف شما تا {end_date} معتبر است.\nبا آرزوی سلامتی',
    },
    {
        'name': 'اعلام تعطیلات',
        'title': 'اطلاع‌رسانی تعطیلات',
        'category': 'holiday',
        'body': 'با سلام\nبدینوسیله تعطیلات {holiday_name} از تاریخ {start_date} تا {end_date} اعلام می‌شود.\nلطفاً برنامه‌ریزی لازم را داشته باشید.\nبا تشکر',
    },
    {
        'name': 'گزارش تولید روزانه',
        'title': 'گزارش تولید امروز',
        'category': 'general',
        'body': 'گزارش تولید {date}:\n\nتعداد تولید: {count} عدد\nمحصول: {product_name}\nوضعیت: {status}\n\nبا تشکر',
    },
    {
        'name': 'یادآوری جلسه',
        'title': 'یادآوری جلسه کاری',
        'category': 'general',
        'body': 'جناب {name}\nیادآوری جلسه {meeting_title}\nزمان: {date} ساعت {time}\nمکان: {location}\nلطفاً حضور به هم رسانید.',
    },
    {
        'name': 'پیامک خوشامدگویی',
        'title': 'خوشامدگویی به مشتری جدید',
        'category': 'promotion',
        'body': '{customer} عزیز، خوش آمدید!\nبا عضویت در {company} از مزایای ویژه بهره‌مند شوید.\nبرای مشاهده لیست محصولات به سایت ما مراجعه کنید.\nبا تشکر',
    },
    {
        'name': 'اعلام موجودی',
        'title': 'اعلام موجود شدن کالا',
        'category': 'new_product',
        'body': 'مشتری گرامی {customer}\nمحصول مورد نظر شما ({product_name}) مجدداً موجود شد.\nتعداد موجود: {stock} {unit}\nعجله کنید!\nبا تشکر',
    },
]


class Command(BaseCommand):
    help = 'ساخت قالب‌های آماده پیامک'

    def handle(self, *args, **options):
        created_count = 0
        for tpl in TEMPLATES:
            obj, created = SMSTemplate.objects.get_or_create(
                name=tpl['name'],
                defaults=tpl,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  + {tpl["name"]}'))
            else:
                self.stdout.write(f'  - {tpl["name"]} (وجود دارد)')

        self.stdout.write(self.style.SUCCESS(f'\n{created_count} قالب جدید ساخته شد.'))
