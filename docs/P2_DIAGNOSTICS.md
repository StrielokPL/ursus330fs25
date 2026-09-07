# P2: interpretacja diagnostyki

Wersja moda 0.0.5.1, tag 0.0.5.1P2. Pole `[vN]` rozróżnia egzemplarze ciągnika w tej sesji; nie jest trwałym ID zapisu gry.

## Decyzja i wykonanie

`STATE.gear=0` oznacza rozłączenie napędu podczas zmiany. Nie należy liczyć go jako osobnego biegu ani błędu.
`predResult` jest ostatnią prognozą; `CONTROL.predictionAgeMs` podaje jej wiek. `reqReason` również jest ostatnim wpisem kontrolera, a nie nowym zdarzeniem w każdym wierszu.
`CONTROL.decisionLoad`, `decisionLoadSrc` i `decisionRpm` pochodzą z chwili decyzji. `STATE.loadSel` i `filteredLoad` pokazują aktualne pomiary. Nie należy utożsamiać spadku obciążenia podczas rozłączenia sprzęgła z poprawą warunków roboczych.
`candidate`, `predictedRpm`, `predictedLoad` i `gate` opisują ostatnią ocenę wyższego biegu, z wiekiem `candidateAgeMs`. Prognoza momentu wykorzystuje istniejącą krzywą silnika i przełożenia; jest przybliżeniem obciążenia po zmianie, nie pomiarem.
`SHIFT_ACTUAL` zawiera zmianę stanu obserwowaną po `VehicleMotor.updateGear`; `seq` i `eventTimeMs` pozwalają odtworzyć kolejność. `GEAR_EVENT` rejestruje wywołania API setGear; nie obejmuje samodzielnie wszystkich automatycznych zmian.
`reductionCompletedMs` oznacza czas od pierwszego żądania ratunkowej/roboczej redukcji do zaobserwowanego pełnego załączenia. `reductionAgeMs` jest obecny tylko, gdy oczekiwanie trwa. `vetoBeforeMs` i `vetoReleaseAgeMs` ujawniają zwolnienie trzysekundowej blokady. Pamięć nieudanego biegu ma numer wirtualny I/1=1 … II/3=6.

## Koła i wydech

`WHEELS.tireLoadT` jest wynikiem GIANTS `wheel.physics:getTireLoad()`: masa równoważna w tonach. To nie surowa siła w N. `forceSource=unavailable` na kliencie bez lokalnego wheelShape jest poprawnym brakiem danych.
`slip` pochodzi z `physics.netInfo.slip` (GIANTS 0…1), nie jest własnym modelem opony. `angularRadS` jest w rad/s, `suspensionM` i `radiusM` w metrach. Rejestrowane są wszystkie koła: zmniejszenie nacisku i utrata kontaktu przednich kół pomogą ocenić unoszenie przodu. Odstęp 250 ms nie wystarcza do analizy szybkich drgań power hop.
`EXHAUST` pokazuje osobne filtrowanie wizualne: narastanie 200 ms, opadanie 500 ms. `extension=false` oznacza brak aktywnego sterowania efektem dodatku w danej próbce (np. brak moda lub trwający rozruch), nie automatycznie błąd.

## Walidacja

`python3 tests/run.py` sprawdza składnię Lua i scenariusze regresji w modelu kontraktu GIANTS. Alternatywnie `lua tests/regression.lua .`.
`python3 tests/package_check.py --source-only` sprawdza manifest i XML, a wariant z ścieżką ZIP porównuje kod w artefakcie z kodem źródłowym i sprawdza czystość archiwum.
Hooki diagnostyczne zapisują dane w RAM; formatowanie i logowanie działa poza ścieżką napędu. Bufor mieści 128 zmian na pojazd między opróżnieniami; `EVENT_OVERFLOW` sygnalizuje utracone zdarzenia. Nie ukrywa się ich jako kompletnego pomiaru.

P2 wymaga jazdy testowej w FS25 1.21.1.0. Testy izolowane nie potwierdzają fizyki błota, wyglądu dymu ani działania multiplayer. Referencja API: oficjalna dokumentacja GIANTS VehicleMotor, WheelPhysics i Motorized (skrypt 1.20) oraz log P1 z gry 1.21.1.0. Szczegółowa kolejność jazdy znajduje się w opisie prerelease.
