# Реестр источников и границы доказательств

Проверено 24.10.2026. «Без даты» означает, что отдельная дата публикации
на проверенной странице не указана; это не публикация 2026 года.
Дата просмотра всех ссылок — 24.10.2026. Компания описывает собственный продукт:
такой первоисточник подтверждает опубликованные возможности, но не независимую
оценку качества, спроса или удобства. Ссылки на код закреплены полными SHA.

## Проблема и инженерные предпосылки

| ID | Прямой первоисточник | Дата публикации / период данных | Место и применимость |
| --- | --- | --- | --- |
| KG1 | [Нацстатком: производство и распределение электроэнергии](https://stat.gov.kg/ru/news/proizvodstvo-i-raspredelenie-elektroenergii-v-2024-godu/) | 03.10.2025 / 2024 | Вводный абзац, таблица баланса. Национальные выработка, импорт и доля ГЭС; не статистика перерывов здания. «Потреблено — всего» включает потери. |
| KG2 | [IEA: Kyrgyzstan’s power system security policy context](https://www.iea.org/reports/strengthening-power-system-security-in-kyrgyzstan-a-roadmap/kyrgyzstans-power-system-security-policy-context) | Отчёт 30.05.2022 / исторический эпизод 2015–2016, системный контекст до 2020 | Key challenges for strengthening power system security, абзацы о маловодье и зимних отключениях. Исторический факт, не прогноз 2026 года. [Титульная страница с датой](https://www.iea.org/reports/strengthening-power-system-security-in-kyrgyzstan-a-roadmap). |
| KG3 | [ВБ: Electricity Sector… to Benefit…](https://www.worldbank.org/en/news/press-release/2023/01/31/electricity-sector-in-kyrgyz-republic-to-benefit-from-support-from-world-bank-and-the-government-of-switzerland) | 31.01.2023 / год инвентаризации не указан | Абзац About half…: срок службы оборудования. Публикация оценки, не текущая доля неисправностей. |
| KG4 | [IEA: Kyrgyzstan energy profile — Energy security](https://www.iea.org/reports/kyrgyzstan-energy-profile/energy-security) | Отчёт 15.04.2020 / в том числе 2018 | Energy security and diversification. Механизм зимнего риска, не адресная история школы. |
| UN1 | [ООН: Goal 7](https://sdgs.un.org/goals/goal7) | Обновляемая страница, без даты / цель к 2030 | Target 7.1 и indicator 7.1.1. Доступ к электричеству и непрерывность снабжения — разные характеристики. |
| EN1 | [DOE GDO: Microgrid Overview, PDF](https://www.energy.gov/sites/default/files/2024-02/46060_DOE_GDO_Microgrid_Overview_Fact_Sheet_RELEASE_508.pdf) | Каталог 2024-02, точный день не указан / инженерный обзор | PDF с. 2–3: critical loads и островной режим; с. 7: данные и концептуальный проект до закупки. Не нормы КР. |
| EN2 | [EIA CBECS: Table C21, PDF](https://www.eia.gov/consumption/commercial/data/2018/ce/pdf/c21.pdf) | 12.2022 / США, 2018 | PDF с. 1, Education, группы по площади. Средняя годовая электрическая интенсивность, не critical kW, не кыргызская школа. |
| EN3 | [Tesla Powerwall 2 AC, North America, PDF](https://www.tesla.com/sites/default/files/pdfs/powerwall/Powerwall%202_AC_Datasheet_en_northamerica.pdf) | Версия в колонтитуле NA-BACKUP-2019-06-11 / паспортные условия | С. 1, Energy/Power. Пример различия total/usable, kW/kWh и round-trip КПД; не актуальное предложение и не рекомендация 60 Гц оборудования для КР. |
| EN4 | [Signify BN021C LED20S/840 L1200, PDF](https://www.assets.signify.com/is/content/Signify/fp911401842382-pss-en_gb) | 15.04.2023 / паспорт изделия | С. 1, Operating and Electrical, 20 W. Не норматив освещённости и не проект аварийного освещения. |
| EN5 | [Ubiquiti U6 Pro — Technical Specifications](https://techspecs.ui.com/unifi/wifi/u6-pro) | Без даты / паспорт изделия | Hardware, max power consumption. Верхний паспортный предел одной AP; нет профиля здания и сетевых потерь. |
| EN6 | [WHO: electricity and health-care facilities](https://www.who.int/news/item/14-01-2023-close-to-one-billion-people-globally-are-served-by-health-care-facilities-with-no-electricity-access-or-with-unreliable-electricity) | 14.01.2023 / глобальный обзор | Абзац Electricity is needed…: функции надёжного питания. Не местное обследование; глобальные числа на КР не переносились. |
| EN7 | [JRC: PVGIS](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en) | Без даты / справочная страница сервиса | Временные оценки PV и солнечного ресурса. Данные для школы в этой работе не загружались. |

## Конкуренты и рабочие процессы

| ID | Прямой первоисточник | Дата / версия | Место и ограничение |
| --- | --- | --- | --- |
| CO1 | [NLR/NREL REopt web tool](https://reopt.nlr.gov/tool) | Без даты | Описание DER, sizing/dispatch, economics/resilience и ссылки на API/код. Подтверждение возможностей, не наш benchmark. |
| CO2 | [REopt User Manual, PDF](https://reopt.nlr.gov/tool/reopt-user-manual.pdf) | Дата выпуска не установлена; просмотрена текущая доступная копия | §1.2 — free web/API; §3.3 — international use; §8.1 — critical load; §21.5 — ERP. Американские defaults требуют адаптации. Не обещание готового проекта для КР. |
| CO3 | [HOMER: Resilience and grid outages](https://homerenergy.com/docs/knowledgebase/article/resilience-and-grid-outages-in-homer-grid/) | Без даты, статья указывает Grid 1.5.2 | Параметры отключения и разделение critical/noncritical. Версию старой статьи не называть текущей версией продукта. |
| CO4 | [HOMER Grid: How… Models Resilience](https://homerenergy.com/products/grid/docs/latest/how_homer_grid_models_resilience.html) | Руководство 1.9; ©2022 не считается датой публикации | Объяснение outage/non-outage расчётов и допущений. Ограничения описанной версии не приписывать всему современному продукту. |
| CO5 | [HOMER Grid product](https://homerenergy.com/homer-grid) | Без даты | Advanced… tariff modeling; Generate Proposals. Тарифы и клиентские отчёты уже существуют у конкурента. |
| CO6 | [HOMER: Download, install, and license](https://homerenergy.com/docs/knowledgebase/article/homer-grid-download-install-and-license/) | Без даты | Windows MSI, лицензирование, 14-day trial. Доступ не проверялся установкой или покупкой. |
| CO7 | [Xendee DESIGN](https://xendee.com/design) | Без даты | Планирование DER, optimisation, power flow и проектные функции. Описание производителя. |
| CO8 | [Xendee glossary](https://xendee.com/glossary) | Без даты | Critical load, resilience, MILP, multi-node, financial terms. Технические определения, не измерение точности. |
| CO9 | [Xendee DESIGN pricing/access](https://xendee.com/pricing/design) | Без даты; условия просмотрены 24.10.2026 | Annual cloud plans, paid 30-day demo, outage calculations и branded PDF reports. Денежные цены не использованы; условия могут изменяться. |
| BU1 | [Xendee: Cascadia Renewables workflow](https://xendee.com/insights/how-cascadia-renewables-is-growing-their-microgrid-business) | 19.12.2025 / описанный клиентский опыт | Таблицы, почасовые нагрузки, моделирование и предложения. Рассказ поставщика о своём клиенте, не независимый эксперимент и не интервью LASTLIGHT. |
| BU2 | [ENVIRO: солнечные электростанции](https://enviro.kg/solar-power-station.html) | Без даты | Публичное местное предложение расчёта/проектирования/установки PV и аккумуляторов. Не подтверждает продажи, размер рынка, ценность нашего ПО или willingness to pay. |

## Код и эксперименты

| Источник | Закреплённая версия | Что проверено |
| --- | --- | --- |
| [PR6, physics](https://github.com/pablo228sos/lastlight/pull/6) | `ef23a710ecb7b235ea734171730a4656c40f4615` | `MODEL.md`, `RELEASE.md`, неизменённые engine/schemas; 75 новых вызовов в sensitivity study. SHA-256 исходников в `research/engineering_evidence/engine_pin.json`. |
| [PR7, ML/frontier](https://github.com/pablo228sos/lastlight/pull/7) | `7147b3f1d0808886c1ca7dc5954ba94edc1564bd` | PRODUCT/ENGINEERING/DATA_PROVENANCE/MODEL_CARD_FRAGILITY, сырые confusion matrices и benchmark. Проверена арифметика опубликованных результатов; обучение не повторялось. |
| [PR8, интеграция](https://github.com/pablo228sos/lastlight/pull/8) | `92613f0b39eec32813a438883e7d4fca18bce0e2` | `physics.ts`, `usePhysicsRun.ts`, integration docs, тесты и fixture pairs; сравнение сохранённых JSON с PR6 побайтно. Production/Windows матрица этим не подтверждена. |

Типы доказательств в пакете различаются явно: национальная статистика;
опубликованный исторический анализ; паспорт изделия; предположение сценария;
расчёт движка; опубликованный synthetic ML benchmark; коммерческая гипотеза;
план будущего пилота. Ссылки на поставщиков не служат доказательством превосходства
LASTLIGHT, а энергобаланс страны — доказательством отключений выбранной школы.
