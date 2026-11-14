# سجل تجهيز الأصول

تاريخ التنفيذ: 13 نوفمبر 2026. الملفات دي تجهيزات ومقترحات للمراجعة؛ مفيش دمج في التطبيق أو اعتماد فني نهائي.

## Landing Pad من المرجع — منصة دائرية وRamp وإشارات هبوط

- تاريخ التسليم: 14 نوفمبر 2026. المرجع: صورة المستخدم للمنصة الدائرية الرمادية ذات حلقات التوجيه البرتقالية والحواف الكريمية وأربع منارات وRamp.
- الإنشاء/الإذن: Codex وPython داخل Blender 5.3.0؛ Geometry وخامات إجرائية أُنشئت للمشروع بناءً على طلب المستخدم ومرجعه. لا توجد موديلات أو Textures أو خدمات توليد خارجية مرفقة.
- المصدر: `source/landing-pad-reference-module.blend`؛ المشهد `Landing Pad / Reference Circular Platform`.
- الموديل: `buildings/landing-pad-reference-module.glb`، مستقل، 5,960,460 بايت، Y-up، متر.
- المعاينات: `previews/landing-pad-reference-module.png` بحجم 1600×900 و`previews/landing-pad-reference-module-top.png` بحجم 1200×1200؛ Render فعلي في Cycles.
- الأجزاء: 48 لوح Deck مستقلًا موزعة على 12 قطاعًا، حلقة توجيه داخلية برتقالية من 24 Segment وحد خارجي برتقالي رفيع، أربعة Deck grilles، وحدات حواف بدرع كريمي وفتحات تهوية وإضاءة، أربع منارات Amber، مسامير وتفاصيل تآكل خفيفة، وRamp مائل بأضلاع Traction وخطوط توجيه وكشافين أماميين.
- المقاس الإجمالي: 14.56×16.91×1.9275 متر (عرض×عمق×ارتفاع)، شامل الـ Ramp والمنارات. الأصل عند مركز المنصة وعلى مستوى Z=0، وأخفض Geometry أعلى منه بحوالي 0.035 متر.
- الهندسة: 465 Node، منها 434 Mesh؛ 144,632 مثلثًا بعد Modifiers، و13 خامة PBR. العلامات والحلقات والشبكات Geometry فعلية، ولا توجد ملفات صور خارجية أو Animation clips.
- الفحص: بنية GLB، الألواح الـ48، المنارات والشبكات، خامات Emission، تمركز حلقة التوجيه عند نصف قطر 2.955–3.205 متر، Geometry خالية من NaN، استبعاد الاستوديو، ثم إعادة استيراد فعلية في Blender وفحص المقاس والمحاور. Raycasts على الـ Ramp أكدت فرق الارتفاع الحقيقي بين نقطتين: Z=0.1927 وZ=0.7535.
- التقارير: `previews/landing-pad-reference-module-validation.json` و`previews/landing-pad-reference-module-report.json`. المصدر الإجرائي: `source/build_reference_landing_pad.py` ثم `source/refine_reference_landing_pad.py`.
- الحالة: مجسم Stylized قابل للتحرير للمراجعة الفنية؛ الأبعاد توضيحية للأصل وليست تصنيفًا لأحمال هبوط حقيقية. لم يتم دمجه في التطبيق أو اعتماده كنسخة Runtime محسنة. ملف Blender يحتفظ بالاستوديو وBloom؛ GLB يحمل الـ Geometry وخامات الإضاءة المحمولة فقط.

## Greenhouse من المرجع — زجاج منحني ومحاصيل وإضاءة نمو

- تاريخ التسليم: 14 نوفمبر 2026. المرجع: صورة المستخدم للصوبة الكريمية والبرتقالية ذات الواجهة الزجاجية المنحنية والباب والمحاصيل والمصابيح الوردية.
- الإنشاء/الإذن: Codex وPython داخل Blender 5.3.0؛ Geometry وخامات إجرائية أُنشئت للمشروع بناءً على طلب المستخدم ومرجعه. لا توجد موديلات أو Textures أو خدمات توليد خارجية مرفقة.
- المصدر: `source/greenhouse-reference-module.blend`؛ المشهد `Greenhouse / Reference Hydroponics`.
- الموديل: `buildings/greenhouse-reference-module.glb`، مستقل، 2,957,320 بايت، Y-up، متر.
- المعاينات: `previews/greenhouse-reference-module.png` بحجم 1536×1024 و`previews/greenhouse-reference-module-rear.png` بحجم 1200×800؛ Render فعلي في Cycles.
- الأجزاء: ست واجهات زجاجية مستمرة ومنحنية، أربعة أقواس هيكلية، نهاية بباب Airlock وRamp، ستة أحواض Hydroponics تحتوي 48 مجموعة نباتات مجسمة، ممر وسطي فعلي، ثلاثة مصابيح نمو Magenta معلقة، HVAC وهوائي وشرائط خدمة فوق السقف، خزان ماء ومضخة وأنابيب خارجية، وفتحات وخدمات خلفية.
- المقاس الإجمالي: حوالي 13.54×6.2517×7.5579 متر (عرض×عمق×ارتفاع)، شامل الـ Ramp وخزان الماء والهوائي. الأصل عند مركز المبنى وعلى مستوى Z=0.
- الهندسة: 219 Node، منها 201 Mesh؛ 108,026 مثلثًا بعد Modifiers، و14 خامة PBR. الزجاج AlphaMode=BLEND؛ مصابيح النمو Emissive. لا توجد ملفات صور خارجية أو Animation clips.
- تفاصيل الداخل: الأحواض ومحاصيلها وسيقانها Geometry فعلية، ولكل حوض مجموعة مستقلة مع Plant count=8. الـ Sill مفرّغ من الداخل بعملية Boolean حتى تظهر جدران الأحواض والممر؛ ملف Blender يحتفظ بـ Cutter مخفي، مستبعد من GLB.
- تأثيرات Blender: إضاءة نمو Area lights وStudio lights وCompositor bloom محفوظة في المصدر، ومستبعدة من GLB؛ المجسم يحتفظ بخامات Emission وشفافية محمولة، وإضاءة العرض تعتمد على الـ Viewer.
- الفحص: بنية GLB، ستة ألواح منحنية شفافة، ستة أحواض وثلاثة Grow fixtures، النباتات، Geometry خالية من NaN، استبعاد الاستوديو والـ Cutter، وإعادة استيراد فعلية في Blender. Raycast أكد تفريغ الـ Sill وإمكانية رؤية أرضية الممر عند Z=0.8875. تم فحص المقاس والمحاور.
- التقارير: `previews/greenhouse-reference-module-validation.json` و`previews/greenhouse-reference-module-report.json`. المصدر الإجرائي: `source/build_reference_greenhouse.py` ثم `source/refine_reference_greenhouse.py`.
- الحالة: تفسير معماري Stylized قابل للتحرير من المرجع، مع استكمال خدمات النهاية الخلفية؛ لم يتم دمجه في التطبيق أو اعتماده كنسخة Runtime محسنة.

## وحدة Life Support من المرجع — مروحة وخزانان ومعالجة داخل نافذة

- تاريخ التسليم: 14 نوفمبر 2026. المرجع: صورة المستخدم للوحدة الكريمية والبرتقالية ذات المروحة والخزانين والأنابيب وكابينة المعالجة.
- الإنشاء/الإذن: Codex وPython داخل Blender 5.3.0؛ Geometry وخامات إجرائية أُنشئت للمشروع بناءً على طلب المستخدم ومرجعه. لا توجد موديلات أو Textures أو خدمات توليد خارجية مرفقة.
- المصدر: `source/life-support-reference-module.blend`؛ المشهد `Life Support / Reference Processing Module`.
- الموديل: `buildings/life-support-reference-module.glb`، مستقل، 2,421,508 بايت، Y-up، متر.
- المعاينات: `previews/life-support-reference-module.png` بحجم 1536×1024 و`previews/life-support-reference-module-rear.png` بحجم 1200×800؛ Render فعلي باستخدام Cycles.
- الأجزاء: كابينة بفواصل Panels ونافذة شفافة داخل تجويف مقطوع فعليًا، ثلاث عبوات معالجة ذات Bands سماوية، مروحة بتسع ريش وPivot مستقل، Yoke وقاعدة، خزانان بتيجان وشرائط Status، وصلات وأنابيب وأكواع مستديرة وحلقات برتقالية، Compressor cassette وفتحات تهوية وهوائيات وقاعدة وأقدام بإضاءة.
- المقاس: 10.4085×6.1082×6.2235 متر (عرض×عمق×ارتفاع)، شامل القاعدة والمروحة والهوائيات. الأصل عند مركز تجميع الوحدة وZ=0، وأخفض Geometry أعلى منه بحوالي 0.04 متر.
- الهندسة: 245 Node، منها 229 Mesh؛ 84,932 مثلثًا بعد Modifiers، و11 خامة PBR. خامة النافذة GLB AlphaMode=BLEND. لا توجد صور خامات خارجية أو Animation clips.
- قابلية التعديل: المروحة وRotor والخزانات والأنابيب والكابينة والفلاتر مجموعات مستقلة. يمكن تدوير Rotor حول Local Z. ملف Blender يحتفظ بـ Boolean cutter مخفي لتعديل تجويف النافذة، وهو مستبعد من GLB.
- الفحص: بنية GLB، المجموعات، عدد الريش والخزانات والفلاتر، الشفافية المحمولة، Geometry خالية من NaN، استبعاد الاستوديو والـ Cutter، إعادة استيراد فعلية في Blender، وفحص المقاس والمحاور. تم Raycast على كابينة GLB للتأكد من أن النافذة تجويف حقيقي؛ أول اصطدام في المنتصف عند Y=-1.26 خلف سطح الواجهة الأصلي Y=-2.05.
- التقرير: `previews/life-support-reference-module-validation.json`. تقرير الإنتاج: `previews/life-support-reference-module-report.json`. المصدر الإجرائي: `source/build_reference_life_support.py`.
- الحالة: تفسير Stylized قابل للتحرير للمراجعة الفنية؛ تفاصيل الظهر مكملة لأسلوب المرجع، ولم يتم دمجه في التطبيق أو اعتماده كنسخة Runtime محسنة.

## وحدة Solar Array من المرجع — ثماني ألواح قابلة للتحرير

- التاريخ: 13 نوفمبر 2026. المرجع: صورة المستخدم لوحدة الألواح الشمسية الكحلية ذات الإطارات الكريمية والحواف البرتقالية ووحدة التحكم المركزية.
- الإنشاء/الإذن: Codex وPython داخل Blender 5.3.0؛ Geometry وخامات إجرائية أُنشئت للمشروع بناءً على طلب المستخدم ومرجعه. لا توجد موديلات أو Textures أو خدمات توليد خارجية مرفقة.
- المصدر: `source/solar-array-reference-module.blend`؛ المشهد `Solar / Reference Twin Array`.
- الموديل: `buildings/solar-array-reference-module.glb`، مستقل، 2,221,180 بايت، Y-up، متر.
- المعاينات: `previews/solar-array-reference-module.png` بحجم 1536×1024 و`previews/solar-array-reference-module-rear.png` بحجم 1200×800؛ Render فعلي في Cycles.
- الأجزاء: صفّان مستقلان Left/Right، بكل واحد أربعة ألواح ضمن شبكة 2×2؛ إجمالي ثمانية ألواح. لكل لوح Frame وخلايا مجسمة 8×8 مع Silver traces وحمايات Corners برتقالية، Rails وJunction box وأسلاك خلفية. الدعامات A-frame، المحاور والأغطية، القواعد والأقدام، ووحدة التحكم والهوائي أجزاء مسماة وقابلة للتحرير.
- المحاور: لكل بنك Pivot مستقل يدور حول Local X عند خط المفصل؛ زاوية العرض الحالية 30°. لا توجد Animation clips؛ الوضع الحالي ثابت، ويمكن تعديل الزاوية يدويًا.
- المقاس: 12.12×4.5875×3.8996 متر (عرض×عمق×ارتفاع). الأصل عند مركز تجميع الوحدة وعلى مستوى Z=0؛ أخفض سطح هندسي أعلى منه بحوالي 0.035 متر.
- الهندسة: 292 Node، منها 274 Mesh؛ 57,072 مثلثًا بعد Modifiers، و12 خامة PBR. الخلايا والشبكات Geometry فعلية، بدون اعتماد على صور Textures.
- الفحص: بنية GLB، ثمانية ألواح مستقلة، ثماني شبكات خلايا 8×8، محورا الميل 30°، الإحداثيات، استبعاد الاستوديو، وإعادة استيراد فعلية في Blender مع فحص المقاس والمحاور — كلها نجحت. التقرير: `previews/solar-array-reference-module-validation.json`.
- المصدر الإجرائي: `source/build_reference_solar_array.py` ثم `source/refine_reference_solar_array.py`. تقرير الإنتاج: `previews/solar-array-reference-module-report.json`.
- الحالة: مجسم Stylized للمراجعة الفنية، مستوحى من المرجع؛ ليس توصيفًا لقدرة كهربائية أو تصميمًا هندسيًا معتمدًا، ولم يتم دمجه في التطبيق أو اعتماده كنسخة Runtime محسنة.

## وحدة Habitat من المرجع — مجسم خارجي قابل للتحرير

- التاريخ: 13 نوفمبر 2026. المرجع: صورة المستخدم لوحدة السكن الكريمية والبرتقالية ذات الباب والقبة والهوائيات والطبق.
- الإنشاء: Codex باستخدام Python وBlender 5.3.0. Geometry وخامات إجرائية أُنشئت للمشروع من المرجع الذي قدمه المستخدم؛ لا توجد موديلات أو خامات صور أو خدمات توليد خارجية مرفقة.
- المصدر: `source/habitat-reference-module.blend`، المشهد `Habitat / Reference Exterior`.
- الموديل: `buildings/habitat-reference-module.glb`، مستقل، 4,038,800 بايت، محاور Y-up ووحدات المتر.
- المعاينة: `previews/habitat-reference-module.png` بحجم 1536×1024 و`previews/habitat-reference-module-rear.png` بحجم 1200×800؛ Render فعلي في Cycles.
- الأجزاء: Pressure hull بفواصل Panels مجسمة، قاعدة وأقدام وفتحات خدمة، نوافذ منحنية بإطارات وجوانات، Airlock بقوس وباب مستقل وStatus lights، Ramp مقسّم مع حواف برتقالية، Skylight بيضاوي وقنطرة برتقالية، Antennas وVents وطبق Parabolic مجوف، وتفاصيل خدمة خلفية مكملة للمرجع.
- المقاس الإجمالي: 13.9304×11.1825×8.0492 متر (عرض×عمق×ارتفاع)، ويشمل الـ Ramp والهوائيات. الأصل عند مركز تجميع الوحدة وعلى مستوى Z=0.
- الهندسة: 220 Node، منها 211 Mesh؛ 188,132 مثلثًا بعد حساب Modifiers، و10 خامات PBR، بدون ملفات Textures خارجية. Animation clips: لا توجد؛ المجسم ثابت وقابل للتحرير.
- الفحص: فحص بنية GLB، المجموعات والأجزاء، خلو الإحداثيات من NaN، استبعاد الأرضية والكاميرات والإضاءة، ثم إعادة استيراد فعلية في Blender وفحص المقاس والمحاور — كلها نجحت. التقرير: `previews/habitat-reference-module-validation.json`.
- تقرير الإنتاج: `previews/habitat-reference-module-report.json`. Scripts: `source/build_reference_habitat.py` ثم `source/refine_reference_habitat.py`.
- الحالة: تفسير خارجي Stylized للمرجع للمراجعة الفنية، مع مصدر مفصل قابل للتحرير. لم يُعتمد بعد كنسخة Runtime محسنة للأداء أو يُدمج في التطبيق. تفاصيل الظهر استكمال إجرائي للمظهر الأمامي.

## المريخ في الفضاء — مشهد ثلاثي الأبعاد من الصورة المرجعية

- التاريخ: 13 نوفمبر 2026. المرجع: صورة المستخدم للمريخ مع النجوم والسديم والصخور المحيطة.
- الإنشاء: Codex وPython داخل Blender 5.3.0. النمذجة والنجوم والصخور والسديم إجرائية؛ خامة الكوكب من المصدر المرخّص المسجل أدناه.
- مصدر Blender: `source/mars-cinematic-scene.blend`، المشهد `Mars / Cinematic Planet`؛ صور الخامات الثلاث مضمّنة داخل الملف.
- المشهد الكامل: `world/mars-cinematic-scene.glb`، 7,371,232 بايت، 25 Node، و20 Mesh، و10 خامات، وثلاث صور مضمّنة؛ 43,500 مثلث بعد Modifiers.
- الكوكب منفصلًا: `world/mars-textured-planet.glb`، 6,267,936 بايت، Mesh واحد وخامة واحدة وصورتان مضمّنتان (Base color وNormal map).
- المعاينة: `previews/mars-cinematic-scene.png`، Render فعلي 1600×900 باستخدام Cycles.
- خامة اللون: `world/mars-global-color-4k.jpg`، 4096×2048، مشتقة من الأصل 8K المحفوظ. Credit: Solar System Scope / INOVE، [المصدر](https://www.solarsystemscope.com/textures/)، [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- الخريطة التوضيحية: `world/mars-illustrative-normal-2k.png`، 2048×1024؛ تم توليدها من تباين اللون وليس من ارتفاعات مقاسة. تحمل نفس Credit ورخصة المصدر.
- السديم: `world/mars-cinematic-nebula-2k.png`، 2048×1152، خامة إجرائية أصلية تم Bake لها من Blender؛ خلفية عرض فنية، وليست صورة فلكية أو تصوير NASA.
- المقاس: الكوكب كرة عرض قطرها 6.4 متر، وليس قطر المريخ الحقيقي. GLB بمحور Y-up ووحدات المتر. الخلفية والصخور جزء من ترتيب فني، وليست مواقع أو أحجامًا فلكية مقاسة.
- Blender يحتفظ بإضاءة شمس دافئة وإضاءة Fill زرقاء وLimb glow يعتمد على زاوية المشاهدة وCompositor bloom؛ هذه تأثيرات عرض خاصة بـ Blender، والمشهد GLB يحتوي على الـ Geometry والخامات المحمولة والخلفية فقط.
- الفحص: تم فحص GLB للمشهد والكوكب، والخامات المضمّنة وCredit داخل Extras، وأعيد استيراد الملفين فعليًا في Blender مع فحص المقاس والمحاور وأبعاد صور الخامات. التقرير: `previews/mars-cinematic-scene-validation.json`.
- المصدر الإجرائي: `source/build_cinematic_mars.py` ثم `source/refine_cinematic_mars.py`. تقرير الإنتاج: `previews/mars-cinematic-scene-report.json`. بيانات Credit مختصرة: `world/mars-texture-credits.md`.
- الحالة: مشهد وGlobe قابلان للتحرير للمراجعة؛ الخريطة معالجة للعرض وليست منتج NASA خامًا، ولم يتم دمجهما في التطبيق. لا توجد Animation clips.

## شخصية المستكشف من المرجع — مجسم علوي ثلاثي الأبعاد

- التاريخ: 13 نوفمبر 2026. المرجع: صورة الشخصية ذات الشعر البني والنظارة والبدلة الكريمية والبرتقالية التي قدمها المستخدم في المحادثة.
- الإنشاء: Codex وPython داخل Blender 5.3.0. المجسم تفسير Stylized للمرجع وليس نسخة مطابقة للملامح أو تصفيفة الشعر.
- المصدر/الإذن: Geometry وخامات إجرائية أُنشئت للمشروع استجابة لطلب المستخدم وبالاستناد إلى مرجعه. لا توجد موديلات أو Textures أو خدمات توليد خارجية مرفقة.
- المصدر القابل للتحرير: `source/explorer-reference-bust.blend`، المشهد `Explorer / Reference Character Bust`.
- التصدير: `characters/explorer-reference-bust.glb`، مستقل، 5,925,768 بايت، Y-up، متر.
- المعاينات: `previews/explorer-reference-bust.png` بحجم 1200×1400 و`previews/explorer-reference-bust-back.png` بحجم 800×1000؛ PNG شفافة من Render فعلي في Cycles.
- الأجزاء: رأس وملامح وجه متصلة، أذنان ورقبة، عيون بنية وجفون وحاجبان وابتسامة، نظارة بإطار وأذرع مجسمة، شعر بني بموجات وخصل إجرائية، بدلة عالية الياقة وتفاصيل برتقالية، أحزمة وأبازيم وحقيبة ظهر وجهاز صدر وجيب.
- المقاس: 1.1088×0.5989×1.5294 متر (عرض×عمق×ارتفاع). الأصل هو نقطة تجميع الـ Bust، ويمكن تغيير الحجم من الـ Root.
- الهندسة: 410 Nodes، منها 402 Meshes، و257,644 مثلثًا بعد حساب Modifiers، و24 خامة. Animation clips: لا توجد؛ مجسم ثابت للمراجعة والتعديل.
- الخامات: PBR وألوان Vertex colors للبشرة والـ Iris، بدون ملفات صور خارجية. خامة النسيج الإجرائية موجودة في Blender؛ تفاصيلها ليست خرائط مخبوزة في GLB.
- الفحص: بنية GLB، استقلال الملفات، المجموعات، ألوان البشرة والعيون، استبعاد إضاءة وكاميرا الاستوديو، إعادة استيراد فعلية في Blender، والأبعاد والمحاور — كلها نجحت. التقرير: `previews/explorer-reference-bust-validation.json`.
- تقرير الإنتاج: `previews/explorer-reference-bust-report.json`. Scripts محفوظة في `source/build_explorer_reference_bust.py` ثم `refine_explorer_reference_bust.py` ثم `finish_explorer_reference_bust.py` ثم `groom_explorer_reference_bust.py`.
- الحالة: أصل مفصل قابل للتحرير للمراجعة الفنية، ولم يتم دمجه في التطبيق أو اعتماده كنسخة نهائية محسنة للأداء. الخلفية والجزء غير الظاهر من الجسم ليسا ضمن النطاق؛ تفاصيل الظهر استكمال إجرائي.

## الروبوت من الصورة المرجعية — مجسم علوي قابل للتحرير

- التاريخ: 13 نوفمبر 2026. المرجع: صورة الروبوت الكريمي والأخضر التي أرسلها المستخدم في المحادثة.
- الإنشاء: Codex باستخدام Blender 5.3.0 وPython. تمت النمذجة الإجرائية محليًا في Scene مستقلة؛ لا توجد موديلات أو خامات صور أو خدمات توليد خارجية.
- الإذن/الاستخدام: تم إنشاء المجسم للمشروع بطلب المستخدم ومن مرجعه المقدم؛ لا توجد أصول خارجية مرفقة تتطلب Credit مستقلًا.
- المصدر: `source/nova-reference-robot-bust.blend`؛ المشهد `NOVA / Reference Robot Bust`.
- الموديل: `characters/nova-reference-robot-bust.glb`، ملف مستقل بحجم 3,533,988 بايت، Y-up، متر.
- المعاينات: `previews/nova-reference-robot-bust.png` بحجم 1200×1400 و`previews/nova-reference-robot-bust-back.png` بحجم 800×1000؛ PNG بخلفية شفافة، Render فعلي باستخدام Cycles.
- النطاق: الجزء العلوي الظاهر في الصورة، بما فيه الرأس والوجه والأذنان والهوائيات والرقبة والصدر والذراعان. الهيئة تفسير ثلاثي الأبعاد للمرجع؛ التفاصيل الخلفية استكمال إجرائي للمجسم.
- الخامات والوجه: هيكل كريمي، أجزاء زيتونية، وصلات Graphite، وجه داكن حجمي، بياض عينين وIris وPupils وCatchlights مجسمة، حاجبان وابتسامة وإشارات مضيئة. ألوان الـ Iris محفوظة كـ Vertex colors في GLB.
- المقاس: 1.2544×0.6756×1.7696 متر (عرض×عمق×ارتفاع). الأصل عند مركز تجميع الجزء العلوي، وليس عند أخفض نقطة.
- المجسمات: 120 Node، منها 110 Meshes؛ 165,908 مثلثات بعد حساب Modifiers، و16 خامة. Animation clips: لا يوجد؛ المجسم ثابت وقابل للتحرير.
- الفحص: اجتاز GLB فحص البنية والمجموعات والألوان والاستقلال عن ملفات خارجية، وأعيد استيراده في Scene فارغة؛ تم التأكد من الأبعاد والمحاور. التقرير: `previews/nova-reference-robot-bust-validation.json`، وتقرير الإنتاج: `previews/nova-reference-robot-bust-report.json`.
- Scripts المصدر: `source/build_nova_reference_robot.py` ثم `source/refine_nova_reference_robot.py` ثم `source/finish_nova_reference_robot.py`؛ ملف Blender الجاهز هو المصدر النهائي للتعديل.
- الحالة: جاهز للمراجعة كأصل ثلاثي الأبعاد، ولم يتم دمجه في التطبيق أو اعتماده كنسخة نهائية محسنة للأداء.

## مشهد القاعدة من الصورة المرجعية — تم التنفيذ في Blender

- تاريخ الإنشاء: 13 نوفمبر 2026.
- المرجع: صورة قاعدة المريخ التي أرسلها المستخدم في المحادثة. المشهد تفسير ثلاثي الأبعاد للمراجعة، وليس تحويلًا مطابقًا لكل بكسل.
- الإنشاء: Codex باستخدام Python داخل Blender 5.3.0 عبر Blender MCP؛ Geometry إجرائية للمشروع، بدون موديلات أو خامات أو خدمات توليد خارجية.
- الإذن/الاستخدام: تم الإنشاء للمشروع بناءً على طلب المستخدم والصورة المرجعية المقدمة منه؛ لا توجد أصول خارجية مرفقة تتطلب Credit منفصلًا.
- المصدر القابل للتحرير: `source/mars-reference-outpost.blend`.
- التصدير: `world/mars-reference-outpost.glb`، حجم 6,797,780 بايت، GLB مستقل، محاور Y-up، وحدات بالمتر.
- المعاينة: `previews/mars-reference-outpost.png`، Render فعلي 1600×900 باستخدام Cycles.
- الأجزاء: Terrain، Habitat، Greenhouse، Laboratory، Hangar، Command، LifeSupport، SolarArray، Communications، Rover، Connectors، Props؛ كل مجموعة مسماة وقابلة للتحرير بشكل مستقل.
- المقاس الكلي مع التلال المحيطة: حوالي 290×285.4×25.46 متر داخل Blender (Z-up).
- عدد المثلثات: 226,706 مع حساب تكرار المجسمات؛ 217,358 في Meshes الفريدة داخل GLB. الخامات: 30. لا توجد Animation clips أو صور Textures خارجية.
- الخامات: ألوان PBR وVertex colors في GLB؛ Blender يحتوي أيضًا على خامة رمل إجرائية وإضاءة وكاميرا للمعاينة. التفاصيل الإجرائية الخاصة بـ Blender ليست خرائط خامات مخبوزة للتطبيق.
- الفحص: فحص بنية GLB نجح، وتمت إعادة استيراد الملف في Scene مستقلة وفحص المجموعات والحدود والمحاور. التقارير: `previews/mars-reference-outpost-report.json` و`previews/mars-reference-outpost-glb-validation.json` و`previews/mars-reference-outpost-reimport.json`.
- Scripts: `source/build_reference_outpost.py` ثم `source/refine_reference_outpost.py` ثم `source/polish_reference_outpost.py`. ملف Blender هو المصدر الحالي الجاهز للفتح؛ لا تحتاج لإعادة التوليد لمراجعته.
- الحالة: مشهد مراجعة مفصل مستوحى من الصورة، لم يتم دمجه في التطبيق أو اعتماده كنسخة نهائية محسنة للأداء. الأرض توضيحية وليست بيانات NASA. واجهة الصورة والشخصية ليستا جزءًا من الموديل.
- ملاحظة على السجل القديم أدناه: هذا المشهد تم إنشاؤه الآن؛ Script الـ Batch A القديم لم يتم تشغيله، ووصف عدم وجود Blender/MCP أدناه يخص مرحلة التجهيز السابقة.

## خريطة المريخ — تم التنزيل وفحص الملف

- الملف: `source/8k_mars.jpg`.
- المصدر: [Solar System Scope](https://play.solarsystemscope.com/textures/).
- رابط التنزيل: https://play.solarsystemscope.com/textures/download/8k_mars.jpg
- الرخصة حسب صفحة المصدر: CC BY 4.0.
- Credit: Solar System Scope / INOVE؛ خريطة بصرية معالجة مبنية على مصادر تصوير/ارتفاعات، وقد تتضمن أجزاء توضيحية بحسب وصف المزود.
- المقاس الفعلي: 8192×4096، JPEG، RGB، وحجم الملف 8,396,951 بايت.
- التعديل: لا يوجد؛ النسخة الأصلية محفوظة كما نزلت. تم فتح الملف وفحص شكله وأبعاده.
- الحدود: مش منتج NASA خام، ومش ارتفاعات أو تحديد موقع دقيق. اتجاه/إحداثيات المنتج لم يتم اعتمادها للاستخدام العلمي.
- نسخة `world/mars-global-color-4k.jpg` بحجم 4096×2048 تم تجهيزها الآن داخل Blender؛ الأصل 8K محفوظ كما هو، والتغييرات وCredit موثّقة في قسم المشهد أعلاه.
- المقاس والمصدر وSHA-256 محفوظين كمان في `source/mars-map-source.json`.

## الأصوات — 8 ملفات أصلية جاهزة للمراجعة بالسماع

المصدر: إنشاء إجرائي أصلي للمشروع باستخدام `source/generate_audio.py`. مفيش Samples أو ألحان أو تسجيلات أشخاص من مصدر خارجي. مش تسجيلات NASA أو أصوات مريخ مقاسة. دي مؤثرات مبدئية قابلة للاستبدال، ومش مكساج نهائي.

| الملف | المدة بالثواني | Channels | الحالة |
| --- | --- | --- | --- |
| `audio/ui-select.wav` | 0.18 | Mono | تم الإنشاء والفحص البنيوي |
| `audio/ui-confirm.wav` | 0.4 | Mono | تم الإنشاء والفحص البنيوي |
| `audio/mission-warning.wav` | 0.8 | Mono | تم الإنشاء والفحص البنيوي |
| `audio/radio-message.wav` | 1 | Mono | تم الإنشاء والفحص البنيوي |
| `audio/discovery.wav` | 1.4 | Mono | تم الإنشاء والفحص البنيوي |
| `audio/rover-loop.wav` | 3 | Mono | تم الإنشاء؛ يلزم مراجعة Loop بالسماع |
| `audio/space-ambience.wav` | 30 | Stereo | تم الإنشاء؛ يلزم مراجعة Loop بالسماع |
| `audio/base-ambience.wav` | 30 | Stereo | تم الإنشاء؛ يلزم مراجعة Loop بالسماع |

كل الملفات PCM WAV، بدقة 48,000 Hz و16-bit. فحص التحميل والمدة والقنوات نجح، ومفيش قمم وصلت لحد Clipping. تم فحص فرق العينات عند طرفي الـ Loops حسابيًا؛ ده لا يغني عن السماع على سماعة أو جهاز حقيقي. التقرير والفحوص/Hashes في `audio/audio-generation-report.json`. الأسماء الموجودة قبل التشغيل لا يتم استبدالها تلقائيًا.

نتائج المدة والقمم وClipped samples الفعلية موجودة في `audio/audio-validation.json`، وحالة Listening review لسه Pending.

## الـ Prompts — جاهزة؛ الصور لم تتولد

- 37 بطاقة Prompt في `references/prompts/*.txt`، مع مسار الحفظ والمقاس والمجموعة والملاحظات.
- فهرس كامل في [Image Prompts.md](../docs/Image%20Prompts.md).
- تشمل صور المراجع، الشخصيات وتعبيراتها، خامة التربة، الشعار، ومراجع اختيارية للمباني والعربية والـ Props.
- الـ Prompts نصوص أصلية لتوجيه الأداة اللي هتستخدمها؛ الصور الناتجة ورخصة أداة الصور يتم توثيقهم وقت تسليمها.

## Blender — Script جاهز؛ التنفيذ لم يحدث

- المصدر: `source/build_batch_a.py`.
- افتراضيًا بيحاول يعمل Habitat فقط؛ بعد مراجعة الشكل، `BUILD = 'batch-a'` يضيف SolarArray وLifeSupport والأرض.
- تم فحص Python syntax. Blender غير متثبت ومفيش Local Blender MCP متوصل، لذلك تنفيذ Blender/GLB/Render **لم يتم اختبارهم**، ومفيش ادعاء إن أي موديل أو Preview اتولد.
- دليل التشغيل: [Blender Direct Steps.md](../docs/Blender%20Direct%20Steps.md).
- طبيعة الناتج المتوقع: نماذج إجرائية توضيحية مبدئية، تحتاج مراجعة فنية ومحاور وخامات وأداء؛ ليست بيانات NASA أو فن نهائي معتمد.
- الـ Script يتخطى مخرجات GLB أو مصدر Draft موجودين بدل استبدالهم.

## لسه مطلوب من المستخدم أو جلسة Blender

1. صور Batch A الأساسية: globe-reference وsurface-reference وcontext-ui-reference وNOVA وAlex وخامة الأرض.
2. تشغيل Habitat Script وإرسال صورته وتقريره، أو توصيل Blender MCP عشان نراجعه سوا.
3. بعد اعتماد الشكل: باقي الموديلات، Maya، وخيارات الصوت/التعبيرات/الشعار.
4. ملفات `preferences.md` والصور النهائية لسه مش متسلمة؛ مجلدات `references/world` القديمة اتسيبت زي ما هي.
