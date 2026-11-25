<div dir="rtl">

# Agent مخصص لـ Power BI Desktop

هذا المستودع يحتوي على **agent** لـ Claude Code متخصص في Power BI Desktop. يعرف DAX و Power Query (M) وتصميم نموذج البيانات (Star Schema) وملفات PBIP (TMDL و PBIR) وتحسين الأداء، ويتصل مباشرة بملف Power BI مفتوح على جهازك ليقرأ النموذج ويضيف المقاييس ويختبرها على بياناتك الفعلية.

## محتويات المستودع

| الملف | الوظيفة |
|---|---|
| `.claude/agents/powerbi-desktop.md` | الـ agent نفسه: خبرته وقواعد عمله ومعاييره في DAX والنمذجة و M |
| `.claude/skills/dax-measure` | كتابة مقياس DAX أو إصلاحه ثم اختباره على البيانات |
| `.claude/skills/model-review` | مراجعة شاملة للنموذج وقائمة إصلاحات مرتبة حسب الأولوية |
| `.claude/skills/power-query` | كتابة وتحسين استعلامات Power Query وحل أخطاء التحديث |
| `.claude/skills/model-docs` | توثيق النموذج كاملاً في `docs/model.md` |
| `.mcp.json` | إعداد خادم Power BI Modeling MCP من Microsoft للاتصال بـ Power BI Desktop |
| `CLAUDE.md` | تعليمات عامة لـ Claude داخل هذا المشروع |

## المتطلبات

- Windows مع **Power BI Desktop** (الاتصال المباشر يعمل على Windows فقط لأن Power BI Desktop لا يعمل إلا عليه).
- **Node.js 18 أو أحدث** (لتشغيل خادم MCP عبر `npx`).
- **Claude Code** مثبت على نفس الجهاز.

## الإعداد

1. انسخ المستودع على جهازك:

</div>

```bash
git clone https://github.com/FashionVue/PowerBI_Report.git
```

<div dir="rtl">

2. افتح ملف التقرير في Power BI Desktop.
3. (مستحسن) احفظ التقرير بصيغة مشروع: **File ← Save as ← Power BI project (.pbip)** داخل مجلد المستودع، حتى يصبح النموذج ملفات نصية يمكن مراجعتها وحفظ نسخها في git. إن لم يظهر الخيار فعّله من **Options ← Preview features ← Power BI Project (.pbip) save option**.
4. شغّل Claude Code من داخل مجلد المستودع:

</div>

```bash
claude
```

<div dir="rtl">

5. عند أول تشغيل سيسألك Claude Code إن كنت تثق بخادم `powerbi-modeling` الموجود في `.mcp.json` — وافق عليه. تأكد من الاتصال بالأمر `/mcp`.
6. **رخصة Microsoft:** خادم Power BI Modeling MCP يتطلب قبول اتفاقية الترخيص (EULA) الخاصة بـ Microsoft قبل الاستخدام: https://go.microsoft.com/fwlink/?LinkId=2381247 — بعد قراءتها يمكنك قبولها بإحدى طريقتين:
   - تعيين متغير البيئة `PBI_MODELING_MCP_ACCEPT_EULA=true` قبل تشغيل `claude`، أو
   - إضافة `--accept-eula` في نهاية قائمة `args` في `.mcp.json`.

   لم أقبلها نيابة عنك عمداً، فهذا قرارك. والـ agent مبرمج على أن يتوقف ويسألك إن طلب الخادم ذلك.

## طريقة الاستخدام

اكتب طلبك بالعربي بشكل طبيعي، وسيستدعي Claude الـ agent تلقائياً، أو اطلبه بالاسم: «استخدم powerbi-desktop ...». أمثلة:

- «اتصل بملف Sales Report المفتوح في Power BI Desktop واعرض لي الجداول والعلاقات»
- «اعمل مقياس نمو المبيعات مقارنة بالسنة الماضية واختبره حسب الشهر»
- «ليش التقرير بطيء؟ راجع النموذج وقل لي وش أصلح أول»
- «حسّن استعلام Power Query لجدول Customers وقل لي أي خطوة تكسر الـ query folding»
- «وثّق النموذج كامل واكتب وصف لكل مقياس ما له وصف»
- «سوّ مراجعة شاملة للنموذج» ← يشغّل `/model-review`

الأوامر المختصرة: `/dax-measure` ، `/model-review` ، `/power-query` ، `/model-docs`

## تجربة سريعة بملف الإكسل التجريبي

في `data/SalesSample.xlsx` بيانات مبيعات وهمية لمتجر أزياء (2024–2025)، فيها 3 جداول: `Sales` (فيه 3,106 طلب)، و`Products`، و`Customers`. والسكربت الذي ولّدها موجود في `data/make_sample.py`.

1. في Power BI Desktop اختر: **Get data ← Excel workbook**، ثم اختر الملف وحدد الجداول الثلاثة (Sales و Products و Customers) واضغط **Load**.
2. شغّل `claude` من مجلد المستودع واكتب الطلبات التالية واحداً بعد الآخر:
   - «اتصل بالملف المفتوح في Power BI Desktop وابنِ نموذج Star Schema: علاقات Sales مع Products و Customers وجدول تاريخ مُعلَّم»
   - «اعمل مقاييس Total Sales و Total Cost و Margin % و Sales YoY %»
   - «اعرض المبيعات حسب السنة، والمبيعات حسب الفئة لسنة 2025»
   - `/model-review`
3. قارن نتائج الـ agent بهذه الأرقام الصحيحة (حسبتها مباشرة من ملف الإكسل):

| المقياس | القيمة الصحيحة |
|---|---|
| Total Sales 2024 | 734,612 |
| Total Sales 2025 | 1,004,890 |
| Sales YoY % (2025) | 36.8% |
| Margin % (لكل سنة) | 60.1% |
| مبيعات 2025 حسب الفئة | Dresses 316,286 · Abayas 277,509 · Thobes 145,087 · Accessories 143,704 · Shoes 122,304 |
| مبيعات 2025 حسب القناة | App 369,412 · Website 332,907 · Store 302,571 |

## طرق وصول الـ agent إلى التقرير

1. **مباشرة إلى Power BI Desktop المفتوح** عبر خادم MCP: يقرأ النموذج ويعدّله ويشغّل استعلامات DAX للتحقق من النتائج. التعديلات تظهر فوراً في Desktop.
2. **ملفات PBIP على القرص**: عندما يكون Desktop مغلقاً، يعدّل ملفات `.tmdl` و PBIR مباشرة. يجب إغلاق Desktop قبل التعديل ثم إعادة فتحه، لأنه لا يقرأ التغييرات أثناء فتح الملف.
3. **ملف ‎.pbix فقط**: لا يمكن تعديله كملف، لذلك يعمل الـ agent عليه مباشرة عبر MCP، أو يطلب منك حفظه كـ PBIP.

## ملاحظات أمان

- **Power BI Desktop لا يستطيع التراجع (Undo) عن التغييرات التي تأتي من أدوات خارجية.** لذلك الـ agent يعرض خطته ويطلب موافقتك قبل أي تعديل جماعي أو حذف أو إعادة تسمية أو تغيير في العلاقات و RLS. احفظ الملف (أو اعمل commit) قبل التعديلات الكبيرة.
- خادم MCP يتصل افتراضياً فقط بـ localhost وبيئة Fabric، ويعمل بصلاحياتك أنت.
- النسخة مثبتة على `@microsoft/powerbi-modeling-mcp@1.0.1`؛ لتحديثها غيّر رقم النسخة في `.mcp.json`.

</div>
