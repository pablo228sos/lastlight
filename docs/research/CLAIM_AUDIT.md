# Аудит научных и продуктовых утверждений LASTLIGHT

Срез 24.10.2026. Проверены исходники и первичные артефакты, без переобучения ML:
[PR6 ef23a71](https://github.com/pablo228sos/lastlight/tree/ef23a710ecb7b235ea734171730a4656c40f4615),
[PR7 7147b3f](https://github.com/pablo228sos/lastlight/tree/7147b3f1d0808886c1ca7dc5954ba94edc1564bd),
[PR8 92613f0](https://github.com/pablo228sos/lastlight/tree/92613f0b39eec32813a438883e7d4fca18bce0e2).
Ветки остаются Draft; наличие кода в PR не означает, что он слит в main.

Статусы: **IMPLEMENTED AND VERIFIED** — реализация с указанной проверкой;
**IMPLEMENTED BUT NOT INTEGRATED** — работает отдельно, но не в согласованном
демонстрационном контуре; **EXPERIMENTAL** — ограниченный исследовательский
результат; **PLANNED** — будущая работа; **UNSUPPORTED** — доказательств нет.
Статус не является сертификацией оборудования или утверждением независимого аудита.

| Утверждение | Код / эксперимент и внешнее подтверждение | Статус | Ограничение | Безопасно сказать жюри |
| --- | --- | --- | --- | --- |
| Детерминированно рассчитывает разряд и энергобаланс | PR6 `services/simulation/engine.py`, `tests/simulation/`; 124 локальных теста, 99,44% покрытия engine/schemas/API; trace содержит потери и residual | IMPLEMENTED AND VERIFIED | Одношиновая квазистационарная модель; не AC-сеть | «Получаем воспроизводимую энергетическую трассу с проверками физических ограничений». |
| Находит критический отказ | PR6: дефицит нагрузки >1e-9 кВт; exact-event trace; [75 новых расчётов](SENSITIVITY_STUDY.md) | IMPLEMENTED AND VERIFIED | Условие заданного сценария, не прогноз аварии сети | «Показываем, когда резерв перестаёт полностью питать выбранные критические нагрузки». |
| 24 кВт·ч дают 9,12 часа | PR6 baseline и независимое C·(SOC0−SOCmin)·η/P | IMPLEMENTED AND VERIFIED | Только при .8/.2/.95/1.5 кВт, без PV и ограничений по мощности | «В нашем синтетическом эталоне первый дефицит через 9,12 часа». |
| 36 кВт·ч гарантируют 13,68 часа в 12-часовом запуске | PR6 comparison: null failure за 12 ч; новые 32 ч отдельно наблюдают 13,68 | UNSUPPORTED в такой формулировке | Горизонт и аналитическая оценка различаются | «В 12-часовом окне отказ не наблюдается; 13,68 часа — отдельный длинный тест/аналитический ориентир». |
| Сцена использует одну физическую трассу | PR8 `physics.ts`, `usePhysicsRun.ts`, tests/physics.spec.ts; pinned PR6 fixture pairs; отдельный Verify зелёный | IMPLEMENTED AND VERIFIED в PR8 | Это проверенная демонстрационная интеграция; независимый production/Windows CI для PR6 не активирован | «SOC, время, нагрузка и свет демонстрационной школы опираются на один результат». |
| Есть явный offline replay | PR8 `?demo=offline`, USE VERIFIED REPLAY, `docs/physics/FRONTEND_INTEGRATION.md` | IMPLEMENTED AND VERIFIED в PR8 | Чтение сохранённого синтетического результата, не новая симуляция с изменёнными параметрами | «При недоступном API можно явно воспроизвести проверенный пример». |
| AI-powered optimization | PR6 сравнивает два заданных улучшения; PR7 содержит классификатор, не глобальный проектный оптимизатор | UNSUPPORTED как общее обещание | Нет оптимизации стоимости/NPV и поиска оптимального оборудования | «Сравниваем инженерные варианты; ML экспериментально предлагает сценарии для физической проверки». |
| Предсказывает blackout risk | PR7 учится условному отказу резерва на synthetic labels | UNSUPPORTED для вероятности отключения реальной сети | Нет обучающей истории аварий КР, калибровки вероятности сетевого события или полевой проверки | «Оценивает результат заданного отключения, а не вероятность его наступления». |
| Realistic digital twin конкретной школы | Геометрия illustrative; нет замеров, BIM/геодезии, счётчиков и калибровки | UNSUPPORTED | Трёхмерная сцена не делает модель обследованным объектом | «Наглядная модель условного объекта для объяснения сценариев». |
| Снижает энергопотребление / гарантирует экономию | Нет полевых before/after, тарифного расчёта и финансового counterfactual | UNSUPPORTED | Снижение unserved critical kWh не равно экономии купленной энергии или денег | «Сравниваем непрерывность питания; экономический эффект ещё нужно измерить». |
| Уникальная технология, аналогов нет | [REopt](https://reopt.nlr.gov/tool), [HOMER](https://homerenergy.com/docs/knowledgebase/article/resilience-and-grid-outages-in-homer-grid/), [Xendee](https://xendee.com/design) уже моделируют DER и resilience | UNSUPPORTED | Нет патентного заключения и сравнительного UX-эксперимента | «Проверяем гипотезу доступного визуального объяснения для небольших объектов и интеграторов». |
| Failure Frontier | PR7 `ml/frontier.py`, `frontier-benchmark.json`: полный trace на SOC-колонку и prefix-классификация | IMPLEMENTED BUT NOT INTEGRATED в официальном PR8 | В PR7 есть своя кандидатная UI; PR8 отмечает frontier как pending; остаются расхождения физики/схем с PR6 | «Есть отдельный исследовательский модуль границы отказа, интеграция ещё согласуется». |
| FragilityNet accuracy 93% | `independent-test.json`: (59+499)/600=.93; baseline .90; 501/600 положительных labels; 2 false negatives | EXPERIMENTAL | Проверены опубликованные матрицы, не повторялось обучение; synthetic test не полевая точность | «93% на 600 отложенных синтетических сценариях; опасные пропуски остаются, физический расчёт обязателен». |
| ML ускоряет frontier | PR7 benchmark: ML .155/.192 с, error 2.18/3.10 ч; exact .038/.053 с, error 0, 17 traces против 80 sampled calls | UNSUPPORTED; опубликованный результат отрицательный | Два отдельных warm CPU опыта, не универсальный закон; разная единица использования traces объяснена в отчёте | «В этом эксперименте точный метод оказался лучше; ускорение ML мы не заявляем». |
| Нейросеть EnergyDNA предсказывает нагрузку местной школы | PR7 реализует статистические Cold Start/Historical baselines на зарубежном BDG2; neural EnergyDNA не обучена | PLANNED для нейросети; baselines EXPERIMENTAL | Whole-building данные не critical-load профиль Кыргызстана | «Подготовлены исследовательские baselines; местная проверка ещё предстоит». |
| Готовая инженерная сертификация / Windows-ready | PR6 local Linux checks; workflow proposal; отдельного Windows production run нет | UNSUPPORTED для сертификации/Windows | Нет presentation-machine приёмки, AC/protection/startup analysis | «Прототип требует проверок оборудования и независимого Windows CI перед эксплуатационными обещаниями». |
| Есть подтверждённый B2B спрос и готовность платить | Публичные предложения поставщиков и модель покупателя; интервью/платных пилотов не было | PLANNED | Существование рынка оборудования не доказывает спрос на наш софт | «Следующий шаг — проверить полезность отчёта на реальных предложениях интеграторов». |

## Проверка ML-метрик и отрицательного результата

Первоисточники: [model card](https://github.com/pablo228sos/lastlight/blob/7147b3f1d0808886c1ca7dc5954ba94edc1564bd/docs/MODEL_CARD_FRAGILITY.md),
[числа test/generalization](https://github.com/pablo228sos/lastlight/blob/7147b3f1d0808886c1ca7dc5954ba94edc1564bd/ml/artifacts/fragility-v1/independent-test.json),
[benchmark](https://github.com/pablo228sos/lastlight/blob/7147b3f1d0808886c1ca7dc5954ba94edc1564bd/ml/artifacts/fragility-v1/frontier-benchmark.json),
[data provenance](https://github.com/pablo228sos/lastlight/blob/7147b3f1d0808886c1ca7dc5954ba94edc1564bd/docs/DATA_PROVENANCE.md).

93% — 558 правильных ответов из 600; dangerous recall = 499/501 ≈99,60%.
Два опасных test-сценария и семь generalization-сценариев пропущены.
Модель всегда должна сопровождаться точной физической проверкой. Даже
константный ответ «опасно» дал бы 83,5% accuracy на этом несбалансированном test;
поэтому одна accuracy не характеризует инженерную безопасность.

Выигрыш ML над logistic baseline не является выигрышем над deterministic
simulator. В двух опубликованных frontier-опытах ML пропустил 51/36 unsafe
cells, exact trace — 0/0. Не скрывать этот результат и не менять обученные модели
для улучшения слайда. Известный exclusive-horizon дефект кандидатной физики PR7
не исправлен зелёным UI CI и ограничивает доверие к пограничным labels.

[Изолированный audit script](../../research/engineering_evidence/audit_repository_evidence.py)
повторно проверяет арифметику обеих confusion matrices и сохраняет
[машиночитаемый отчёт с SHA-256 источников](data/repository_evidence_audit.json).
Это проверка опубликованных метрик, не повторное обучение или новый замер скорости.
При горизонте ровно 9,12 ч PR7 по-прежнему возвращает false failure при шагах
1/15 минут: critical unserved порядка 2,96e-13 / 7,99e-15 кВт·ч; шаг 60 минут
возвращает null. Официальный PR6 во всех трёх шагах возвращает null. Не объединять
версии: исследование использует physics `lastlight-dispatch-1.0.0` / schema `1.0.0`,
а labels FragilityNet `fragility-1-0e9fbf8a5ba1` происходят от candidate physics
`lastlight-dispatch-1.1.0`. Отдельный model version нейросети не является версией физики.

## Непротиворечивость репозитория

`docs/PRODUCT.md` и `docs/ENGINEERING.md` местами описывают прежнюю визуальную
стадию. PR8 уже содержит backend-driven comparison/replay; ранние заметки об их
отсутствии относятся к старым SHA. При этом PR8 прямо оставляет frontier pending.
Для жюри обязательно называть ветку, версию модели и тип данных. Изменять
production-документы и чужие ветки этот исследовательский PR не пытается.

Проверено побайтно: оба PR8 replay JSON совпадают с PR6 fixtures; их SHA-256
сохранены в machine-readable audit. **Сам PR8 не содержит Python backend**:
live demonstration требует отдельного checkout PR6 и доступного API. Это
интеграция по контракту, не объединённый deployment. Тексты и снимки PR8
не являются доказательством физического питания реального здания.

Опубликованное verification evidence:
[PR6 RELEASE](https://github.com/pablo228sos/lastlight/blob/ef23a710ecb7b235ea734171730a4656c40f4615/docs/physics/RELEASE.md)
фиксирует 124 local tests / 99,44% coverage и 20 Linux launcher/HTTP checks;
[PR7 Verify](https://github.com/pablo228sos/lastlight/actions/runs/40084814511)
и [PR8 Verify](https://github.com/pablo228sos/lastlight/actions/runs/40087257236)
успешны на проверенных SHA. Это не approved production physics matrix на Windows.
У [PR6 Verify](https://github.com/pablo228sos/lastlight/actions/runs/40087691841)
и PR8 проверены job conclusions: `web=success`, `reference-physics=success`;
официального production simulation job в этих запусках нет.
Новая проверка этого PR — 75 sensitivity results и artifact audit; полную
production suite здесь повторно не запускали. [API contract](https://github.com/pablo228sos/lastlight/blob/ef23a710ecb7b235ea734171730a4656c40f4615/docs/physics/CONTRACT.md)
и [физическая модель](https://github.com/pablo228sos/lastlight/blob/ef23a710ecb7b235ea734171730a4656c40f4615/docs/physics/MODEL.md)
остаются официальными источниками поведения.
