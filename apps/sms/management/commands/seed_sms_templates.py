from django.core.management.base import BaseCommand
from apps.sms.models import SMSTemplate


TEMPLATES = [
    # ── فاکتور ──────────────────────────────────────────────
    {
        'name': 'صدور فاکتور جدید',
        'title': 'اطلاع‌رسانی صدور فاکتور',
        'category': 'invoice',
        'body': '{name} گرامی،\n\nفاکتور شماره {invoice_number} به مبلغ {total} ریال صادر گردید.\nباقیمانده حساب: {remaining} ریال\n\nلطفاً جهت مشاهده جزئیات به پنل کاربری مراجعه فرمایید.\nبا تشکر - {company_name}',
    },
    {
        'name': 'یادآوری پرداخت فاکتور',
        'title': 'یادآوری پرداخت بدهی',
        'category': 'invoice',
        'body': '{name} گرامی،\n\nاین پیام یادآوری پرداخت بدهی شماست.\nشماره فاکتور: {invoice_number}\nمبلغ معوق: {remaining} ریال\n\nخواهشمند است در اسرع وقت نسبت به تسویه حساب اقدام فرمایید.\n{company_name}',
    },
    {
        'name': 'تایید پرداخت فاکتور',
        'title': 'تایید دریافت پرداخت',
        'category': 'invoice',
        'body': '{name} گرامی،\n\nپرداخت شما برای فاکتور {invoice_number} با موفقیت ثبت شد.\nمبلغ پرداختی: {paid_amount} ریال\nباقیمانده: {remaining} ریال\n\nبا تشکر از پرداخت به موقع - {company_name}',
    },
    {
        'name': 'پیش‌فاکتور',
        'title': 'ارسال پیش‌فاکتور',
        'category': 'invoice',
        'body': '{name} گرامی،\n\nپیش‌فاکتور شماره {invoice_number} برای شما صادر شد.\nمبلغ کل: {total} ریال\n\nجهت تایید و صدور فاکتور نهایی با ما تماس بگیرید.\n{company_name}',
    },

    # ── سفارش ──────────────────────────────────────────────
    {
        'name': 'تایید سفارش',
        'title': 'تایید دریافت سفارش',
        'category': 'order',
        'body': '{name} عزیز،\n\nسفارش شماره {order_number} با موفقیت ثبت شد.\nزمان تقریبی آماده‌سازی: {delivery_time}\n\nاز اعتماد شما سپاسگزاریم.\n{company_name}',
    },
    {
        'name': 'ارسال سفارش',
        'title': 'اطلاع‌رسانی ارسال سفارش',
        'category': 'order',
        'body': '{name} گرامی،\n\nسفارش شماره {order_number} ارسال شد.\nکد رهگیری: {tracking_code}\n\nبا تشکر - {company_name}',
    },
    {
        'name': 'آماده تحویل سفارش',
        'title': 'آمادگی تحویل سفارش',
        'category': 'order',
        'body': '{name} عزیز،\n\nسفارش شماره {order_number} آماده تحویل است.\nلطفاً جهت دریافت به انبار مراجعه فرمایید.\n\n{company_name}',
    },

    # ── تخفیف ──────────────────────────────────────────────
    {
        'name': 'تخفیف ویژه مشتریان',
        'title': 'پیشنهاد ویژه برای شما',
        'category': 'discount',
        'body': '{name} گرامی،\n\nویژه شما! تخفیف ویژه {discount}٪ روی تمامی محصولات.\nاز {start_date} تا {end_date}\n\nجهت بهره‌مندی با شماره ۰۲۱-۱۲۳۴۵۶۷۸ تماس بگیرید.\n{company_name}',
    },
    {
        'name': 'کد تخفیف اختصاصی',
        'title': 'کد تخفیف شما',
        'category': 'discount',
        'body': '{name} عزیز،\n\nکد تخفیف اختصاصی شما: {discount_code}\nمبلغ تخفیف: {discount_amount} ریال\n اعتبار تا: {end_date}\n\nبا وارد کردن این کد در هنگام خرید از تخفیف بهره‌مند شوید.\n{company_name}',
    },
    {
        'name': 'فروش ویژه پایان فصل',
        'title': 'حراج پایان فصل',
        'category': 'discount',
        'body': '{name} گرامی،\n\nحراج بزرگ پایان فصل شروع شد!\nتا {discount}٪ تخفیف روی محصولات منتخب\nاز {start_date} تا {end_date}\n\n فرصت محدود است!\n{company_name}',
    },

    # ── پرداخت ──────────────────────────────────────────────
    {
        'name': 'یادآوری پرداخت',
        'title': 'یادآوری پرداخت بدهی',
        'category': 'payment',
        'body': '{name} گرامی،\n\nمبلغ {amount} ریال بابت فاکتور شماره {invoice_number} معوق است.\nخواهشمند است در اسرع وقت نسبت به پرداخت اقدام فرمایید.\n\nبا تشکر - {company_name}',
    },
    {
        'name': 'تسویه حساب کامل',
        'title': 'تایید تسویه حساب',
        'category': 'payment',
        'body': '{name} گرامی،\n\nحساب شما با موفقیت تسویه شد.\nمبلغ پرداختی: {amount} ریال\nوضعیت: تسویه کامل ✓\n\nاز همکاری شما سپاسگزاریم.\n{company_name}',
    },

    # ── محصول جدید ──────────────────────────────────────────
    {
        'name': 'معرفی محصول جدید',
        'title': 'محصول جدید در فروشگاه',
        'category': 'new_product',
        'body': '{name} گرامی،\n\nمحصول جدید {product_name} به مجموعه محصولات اضافه شد!\nقیمت: {price} ریال\n\nجهت سفارش با ما در تماس باشید.\n{company_name}',
    },
    {
        'name': 'اعلام موجودی مجدد',
        'title': 'موجود شدن کالا',
        'category': 'new_product',
        'body': '{name} عزیز،\n\nمحصول مورد نظر شما ({product_name}) مجدداً موجود شد.\nتعداد موجود: {stock} عدد\n\nعجله کنید، موجودی محدود است!\n{company_name}',
    },
    {
        'name': 'گالری محصولات',
        'title': 'معرفی جدیدترین محصولات',
        'category': 'new_product',
        'body': '{name} گرامی،\n\nجدیدترین محصولات {company_name}:\n• {product_name} - {price} ریال\n\nبرای مشاهده کامل محصولات به سایت ما مراجعه کنید.\nبا تشکر',
    },

    # ── تولد ──────────────────────────────────────────────
    {
        'name': 'تبریک تولد',
        'title': 'تبریک تولد مشتری',
        'category': 'birthday',
        'body': '{name} عزیز،\n\nتولدتان مبارک! 🎂\n\nبرای قدردانی از همراهی شما، تخفیف ویژه {discount}٪ در نظر گرفته شد.\nکد تخفیف: {discount_code}\nاعتبار تا: {end_date}\n\nبا آرزوی سلامتی و شادی\n{company_name}',
    },

    # ── تعطیلات ──────────────────────────────────────────
    {
        'name': 'اعلام تعطیلات نوروز',
        'title': 'تعطیلات نوروزی',
        'category': 'holiday',
        'body': '{name} گرامی،\n\nبدینوسیله تعطیلات نوروزی اعلام می‌شود.\nاز {start_date} تا {end_date}\n\nپیشاپیش نوروزتان پیروز.\n{company_name}',
    },
    {
        'name': 'تعطیلات رسمی',
        'title': 'اطلاع‌رسانی تعطیلات',
        'category': 'holiday',
        'body': 'با سلام\n\nتعطیلات {holiday_name} از تاریخ {start_date} تا {end_date} می‌باشد.\nلطفاً برنامه‌ریزی لازم را داشته باشید.\n\n{company_name}',
    },

    # ── تبلیغاتی ──────────────────────────────────────────
    {
        'name': 'پیامک خوشامدگویی',
        'title': 'خوشامدگویی به مشتری جدید',
        'category': 'promotion',
        'body': '{name} عزیز، خوش آمدید!\n\nبا عضویت در {company_name} از مزایای ویژه بهره‌مند شوید.\n- تخفیف ویژه اولین خرید\n- پشتیبانی اختصاصی\n- ارسال رایگان\n\nبا تشکر',
    },
    {
        'name': 'دعوت به همکاری',
        'title': 'دعوت به همکاری تجاری',
        'category': 'promotion',
        'body': '{name} گرامی،\n\n{company_name} از شما دعوت به همکاری می‌کند.\nشرایط ویژه همکاری:\n- تخفیف {discount}٪ برای خریداران عمده\n- ارسال رایگان سفارشات بالای {min_order} ریال\n\nجهت کسب اطلاعات بیشتر تماس بگیرید.',
    },
    {
        'name': 'مسابقه و قرعه‌کشی',
        'title': 'مسابقه ویژه مشتریان',
        'category': 'promotion',
        'body': '{name} عزیز،\n\nمسابقه بزرگ {company_name} شروع شد!\nجایزه ویژه: {prize}\nشرکت در مسابقه: ارسال کد {discount_code}\n\nبرندگان {end_date} اعلام می‌شوند.\nموفق باشید!',
    },

    # ── عمومی ──────────────────────────────────────────────
    {
        'name': 'یادآوری جلسه',
        'title': 'یادآوری جلسه کاری',
        'category': 'general',
        'body': '{name} گرامی،\n\nیادآوری جلسه {meeting_title}\nزمان: {date} ساعت {time}\nمکان: {location}\n\nلطفاً حضور به هم رسانید.',
    },
    {
        'name': 'گزارش تولید روزانه',
        'title': 'گزارش تولید امروز',
        'category': 'general',
        'body': 'گزارش تولید {date}:\n\nتعداد تولید: {count} عدد\nمحصول: {product_name}\nوضعیت: {status}\n\nبا تشکر',
    },
    {
        'name': 'اعلام تغییر قیمت',
        'title': 'تغییر قیمت محصولات',
        'category': 'general',
        'body': '{name} گرامی،\n\nضمن عرض ادب، به استان می‌رساند قیمت محصول {product_name} از {old_price} به {new_price} ریال تغییر یافت.\nتاریخ اجرا: {date}\n\n{company_name}',
    },
    {
        'name': 'پیامک پیگیری',
        'title': 'پیگیری رضایت مشتری',
        'category': 'general',
        'body': '{name} گرامی،\n\nآیا از خدمات {company_name} راضی بودید؟\nنظرات شما برای ما ارزشمند است.\n\nبرای ارسال نظر عدد ۱ را به همین شماره پیامک کنید.\nبا تشکر',
    },
    {
        'name': 'اعلام آدرس جدید',
        'title': 'تغییر آدرس دفتر مرکزی',
        'category': 'general',
        'body': '{name} گرامی،\n\nآدرس جدید دفتر مرکزی {company_name}:\n{address}\n\nتلفن: {phone}\n\nاز توجه شما سپاسگزاریم.',
    },
    {
        'name': 'پیامک قدردانی',
        'title': 'قدردانی از مشتری',
        'category': 'general',
        'body': '{name} عزیز،\n\nاز اعتماد و همراهی صمیمانه شما سپاسگزاریم.\n{company_name} همواره در کنار شماست.\n\nبا آرزوی موفقیت و سربلندی',
    },
]


class Command(BaseCommand):
    help = 'ساخت قالب‌های آماده پیامک با داده‌های نمونه'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for tpl in TEMPLATES:
            obj, created = SMSTemplate.objects.get_or_create(
                name=tpl['name'],
                defaults=tpl,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  + {tpl["name"]}'))
            else:
                # اگر قالب از قبل وجود دارد، body را آپدیت کن
                if obj.body != tpl['body']:
                    obj.body = tpl['body']
                    obj.title = tpl['title']
                    obj.category = tpl['category']
                    obj.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'  ~ {tpl["name"]} (بروزرسانی شد)'))
                else:
                    self.stdout.write(f'  - {tpl["name"]} (وجود دارد)')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'  {created_count} قالب جدید ساخته شد'))
        if updated_count:
            self.stdout.write(self.style.WARNING(f'  {updated_count} قالب بروزرسانی شد'))
        self.stdout.write(self.style.SUCCESS(f'  مجموع: {created_count + updated_count} قالب'))
