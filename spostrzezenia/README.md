# Ursus C-330 / C-330M — spostrzeżenia, changelog i rejestr problemów

Stan opracowania: 7 września 2026. Ostatnie udokumentowane wydanie: **0.0.5.0P1**. Niniejszy plik jest historią techniczną projektu, a nie deklaracją, że wszystkie opisane poprawki zostały już zatwierdzone w grze.

## 1. Zasady prowadzenia dokumentacji

Rozróżniamy cztery stany: **zaobserwowane** (objaw potwierdzony logiem lub relacją z testu), **zdiagnozowane** (ustalono przyczynę), **załatane — do testu** (kod lub paczka opublikowane, ale nie ma jeszcze wiarygodnego testu potwierdzającego rezultat) oraz **potwierdzone** (późniejszy test wykazał oczekiwane zachowanie). Udany build GitHub Actions potwierdza budowę i kontrolę paczki, nie poprawność działania Lua w FS25. Nie należy oznaczać problemu jako zamkniętego tylko dlatego, że opublikowano prerelease.

Źródła: przesłane logi z testów C-330/C-330M, ich wcześniejsze analizy, kod i historia commitów repozytorium oraz opisy wydań. Przykłady tabelaryczne poniżej są transkrypcją wcześniej odczytanych wartości diagnostycznych; nie są udawanymi, dosłownymi liniami loga. Gdy pełna nazwa pliku lub dokładny timestamp nie zostały zachowane w dokumentacji rozmowy, jest to wyraźnie zaznaczone. Nie dopisujemy brakujących danych z pamięci ani nie traktujemy przybliżenia jako pomiaru.

Repozytorium: https://github.com/StrielokPL/ursus330fs25

Powiązany zestaw narzędzi i materiałów referencyjnych: `StrielokPL/strojenieciagnikowfs25`. Historia innej paczki Ursus 1654/1954 nie jest częścią tego kompendium.

## 2. Punkty odniesienia i historia wydań

### 0.0.4.3 — stabilny punkt C-330

- Commit/tag: `68ddd4c5fc413362c655732c8633b75f27165ac9`.
- SHA-256 paczki: `26b5d2aab910de2bcb76d3fd019b66673b95e3c2e9140ec83dbf0b80afa6faf0`.
- Status: zachowany punkt odniesienia wcześniejszej walidacji C-330. Nie nadpisywać go eksperymentalną kalibracją C-330M.
- Zachowane ustalenia obejmują silnik, przełożenia, fizykę masy i balastu, opony oraz dotychczasowe zabezpieczenia automatycznej skrzyni. Szczegółowe starsze iteracje 0.0.1.x–0.0.4.x należy odtwarzać z historii Git i wcześniejszych archiwów testowych, a nie rekonstruować z niepełnej pamięci.

### 0.0.5.0 — punkt wyjścia C-330M

- Commit/tag oryginalnego wydania: `3393f67c44c3ea105fc43991100b7bdcdc7733a9`.
- Paczka: `FS25_UrsusC330_330M_4x2.zip`, 131 512 352 B.
- SHA-256: `8d10ee02af49db127395db97bf32c6e6c8929e9436d7b100669c379f70254757`.
- C-330M otrzymał kalibrację 30 KM przy 2200 rpm, moment około 100 Nm w użytecznym zakresie i fabrycznie wzorowaną skrzynię 6F/2R z reduktorem I/II.
- Prędkości maksymalne przy 2200 rpm: I/1 2,097; I/2 4,064; I/3 6,491; II/1 8,491; II/2 16,460; II/3 26,290 km/h. Wsteczny: R-I około 1,761 i R-II 7,133 km/h.
- Skalowanie prędkości względem C-330: `26.29 / 22.878 = 1.149138910743946`.
- Zgłoszony problem: C-330M z małym pługiem nie osiągał oczekiwanych około 8 km/h; pozostawał na I/3 przy około 6 km/h. Podniesienie pługa pozwalało przejść na II/1, po czym automat wybierał II/2 i II/3.
- Status: problem diagnozowany; nie uznawać kalibracji roboczej C-330M za zatwierdzoną na podstawie tego wydania.

### 0.0.5.0D1 — pierwsza diagnostyka zintegrowana

- Commit wydania: `194c34a83d8f084f00deffa28a1961e1d9c0b937`.
- Release: https://github.com/StrielokPL/ursus330fs25/releases/tag/0.0.5.0D1
- Dodano `Scripts/C330FullDiagnostic.lua` oraz opcjonalny loader w `Scripts/C330ShopOrder.lua`. Diagnostyka miała rejestrować wynik kontrolera, stan silnika, obciążenia ADS/GIANTS, limity prędkości, biegi, zakresy, narzędzia i tylne koła.
- Wprowadzono politykę: prerelease zawiera diagnostykę; pełne wydanie usuwa jej plik z ZIP-a. Sam loader pozostaje bezpiecznym no-op, gdy pliku nie ma.
- Nie zmieniono silnika, przełożeń ani progów skrzyni. Wewnętrzna wersja modDesc pozostała 0.0.5.0.
- Status: **wycofana z testów z powodu krytycznego błędu diagnostyki**. Nie używać D1 do dalszego strojenia.

### 0.0.5.0D2 — bezpieczny flight recorder

- Commit wydania: `4e12fad3068a6598779e9c447ab345c6768d76cd`.
- Release: https://github.com/StrielokPL/ursus330fs25/releases/tag/0.0.5.0D2
- Paczka: 131 516 772 B, SHA-256 `649acf09364a728d57bf1eb7e22d711892836e223d4fdcee6996fdc0775a9188`.
- Rozdzielono krytyczny hook skrzyni od raportowania. Hook odkłada prymitywne wartości do RAM i zwraca wynik; formatowanie, wywołania dodatkowych API i Logging odbywają się poza ścieżką decyzji.
- Snapshot stanu co 250 ms, narzędzia i koła co 1000 ms; zapis zdarzeń tylko przy istotnych zmianach. Odroczony flush zabezpieczono `pcall`, a awaria pojedynczej diagnostyki ma ją wyłączyć po jednym ostrzeżeniu.
- Usunięto błąd wielowartościowego zwrotu `getSpeedLimit()` przekazywanego do `tonumber()`.
- Status: późniejszy log D2 potwierdził brak powtarzających się wyjątków diagnostycznych i umożliwił wiarygodną analizę skrzyni. Nie oznacza to, że wszystkie możliwe problemy wydajnościowe gry zostały wykluczone.

### 0.0.5.0P1 — governor biegu roboczego i awaryjna redukcja

- Commit: `3f4b2dd145eb3da2b78a296ff66530bf5a49bc10`.
- Release: https://github.com/StrielokPL/ursus330fs25/releases/tag/0.0.5.0P1
- Paczka: 131 520 669 B, SHA-256 `c8d6d4ca0e489bed335340f2cac2ccce4214aeb7ebc231a4ad003519a3876fa9`.
- GitHub Actions: https://github.com/StrielokPL/ursus330fs25/actions/runs/33674116955 — build, kontrola diagnostyki i publikacja zakończone sukcesem.
- Dodano `Scripts/C330TransmissionWorkFix.lua` jako osobną warstwę gameplay po dotychczasowym `C330TransmissionFix.lua`. Zachowano diagnostykę D2. Nie zmieniono krzywych silnika, przełożeń, mas balastu ani fizyki opon.
- Governor wyznacza najwyższy spośród sześciu rzeczywistych biegów, który przy aktywnym limicie pracy daje co najmniej 1500 rpm. Bieg ten staje się sufitem dla automatycznych upshiftów. Przy opuszczeniu narzędzia na zbyt wysokim biegu redukcja przebiega po jednym mechanicznym stopniu.
- Dopuszczono I/3 → II/1 pod obciążeniem roboczym, jeśli II/1 jest właściwym biegiem, RPM ≥2050 i upłynął istniejący dwell 2 s. Usuwa to pułapkę wymogu load ≤0,55 dla tej konkretnej zmiany.
- Dodano awaryjną redukcję przy gazie ≥0,85, load ≥0,75 i RPM ≤1450, z 2,5 s blokadą ponownego upshiftu. Po podniesieniu pracującego narzędzia stosowany jest 2,5 s hold przed powrotem do zmian drogowych.
- Status: **opublikowane, do weryfikacji w grze**. W dostępnych materiałach nie ma późniejszego loga potwierdzającego P1. Wcześniejsza zapowiedź nazwy 0.0.5.1P1 nie była rzeczywistym wydaniem; opublikowany tag i wersja wewnętrzna to 0.0.5.0P1 / 0.0.5.0.

## 3. Szczegółowe analizy błędów z logów

### INC-001 — C-330M nie wychodzi z I/3 podczas orki

**Objaw.** Mały pług z epoki, oczekiwane około 8 km/h. Traktor zatrzymywał się na około 6 km/h nawet przy sprzyjającym terenie. Po podniesieniu pługa następował poprawny mechanicznie I/3 → II/1, ale potem niepotrzebne upshifty II/1 → II/2 → II/3.

**Źródła.** Test 0.0.5.0 z 2 września 2026, m.in. `log(20260902-163918).txt`; wcześniejszy log z 1 września zachował wpisy kontrolera. Pełny surowy log nie jest dołączony do repozytorium.

**Przykład zachowanego wpisu:**

```text
RANGE UP I/3 -> II/1 rpm=2201 load=.308 source=ADS speed=5.81
RANGE DOWN II/1 -> I/3 rpm=735 load=.589 source=ADS speed=3.32
```

**Przyczyna.** W bazowym kontrolerze I/3 → II/1 wymagało jednocześnie RPM ≥2050, load ≤0,55, dwell 2 s i stabilizacji 800 ms. I/3 C-330M ma maksimum 6,491 km/h; jego osiągnięcie nie gwarantuje spadku obciążenia przy orce. Podniesienie pługa obniża load, co odblokowuje zmianę. GIANTS następnie optymalizuje biegi wewnątrz zakresu i nie rozpoznaje, że II/1 jest już właściwym biegiem roboczym.

**Zastosowana poprawka.** P1: work governor i specjalne dopuszczenie I/3 → II/1 pod obciążeniem, gdy II/1 jest wyznaczonym biegiem roboczym. Zachowano próg RPM i dwell. Nie zwiększano sztucznie mocy ani prędkości I/3.

**Status:** załatane — do testu. Wymagany test orki na poziomie, pod górę i po podniesieniu/opuszczeniu pługa.

### INC-002 — D1 powoduje tysiące błędów Lua i zatrzymanie aktualizacji pojazdu

**Objaw.** Duże lagi, ciągnik porusza się, a kamera pozostaje w miejscu; po wejściu do menu użytkownik nie może wrócić do gry. Pojawiały się również nielogiczne przejścia, w tym I/3 → II/3 na C-330.

**Źródło.** Log z testu D1 przesłany 2 września 2026. Wcześniejsza analiza policzyła 3188 wyjątków z linii 124, 2305 wpisów START_GEAR i 1312 DECISION. Dokładna nazwa tego pliku nie została zachowana w niniejszym indeksie.

**Dosłowny komunikat błędu:**

```text
C330FullDiagnostic.lua:124: invalid argument #2 to 'tonumber' (number expected, got boolean)
```

**Przyczyna techniczna.** `getSpeedLimit()` może zwrócić także drugi argument typu boolean. Konstrukcja `tonumber(safeCall(...))` przekazywała oba wyniki do `tonumber`, więc boolean stawał się niedozwolonym argumentem `base`. Wyjątek występował wewnątrz wrappera `findGearChangeTargetGearPrediction()` po wykonaniu logiki kontrolera, ale przed oddaniem jej wyniku silnikowi gry. Mogło to przerwać update po zmianie zakresu, a przed zakończeniem decyzji o biegu. Stąd pozornie niemożliwy stan zakres II + stary gear=3; nie jest to dowód, że bazowy kontroler celowo zażądał I/3 → II/3.

Drugim problemem był synchroniczny zapis tysięcy zdarzeń, czasem co około 16–20 ms. Tego typu logging w krytycznej ścieżce pojazdu jest niedopuszczalny.

**Zastosowana poprawka.** D2: `safeFirst()` zwraca wyłącznie pierwszą wartość API; hooki RAM-only; odroczony, ograniczony częstotliwością flush; ochrona `pcall`; brak dodatkowych odczytów API i formatowania w krytycznej ścieżce. Kontroler skrzyni nie został wtedy zmieniony.

**Rozstrzygnięcie podejrzenia o drugi mod.** Stary `FS25_ZZ_C330FullDiagnostic` występował jako Available mod, lecz nie było odpowiadającego mu `Load mod`. Nie był aktywny w pokazanym teście i nie stanowił przyczyny awarii. Należy go usunąć jako zbędną pozostałość, nie przypisywać mu błędnie winy.

**Status:** przyczyna zdiagnozowana, D2 potwierdził usunięcie powtarzających się wyjątków. Nie przywracać architektury D1.

### INC-003 — C-330 + Brony 5: II/2 → II/3 i zduszenie silnika

**Objaw.** Automat sam wybiera II/3 podczas pracy, po czym ciągnik traci obroty i prędkość. Dopiero ręczne II/3 → II/2 pozwala odzyskać obroty. Problem pojawił się co najmniej trzykrotnie w analizowanym teście.

**Źródło.** Pełny log diagnostyczny D2 przesłany 2 września 2026; dokładna nazwa pliku nie została zachowana w indeksie. Przykład decyzji: 21:10:12.748. Brony 5, opuszczone, limit pracy 15 km/h, masa zestawu około 2,577 t.

| Etap | Bieg / decyzja | km/h | RPM | load |
|---|---|---:|---:|---:|
| przed zmianą | II/2 | 14,33 | 2098 | 0,851 |
| decyzja automatu | II/2 → II/3 | 14,06 | 2126 | 0,755 |
| po zmianie | II/3 | 11,73 | 1399 | 0,542 |
| spadek | II/3 | 11,62 | 1104 | 0,914 |
| dalszy spadek | II/3 | 10,99 | 1003 | 0,974 |
| dalszy spadek | II/3 | 9,38 | 975 | 0,943 |
| dalszy spadek | II/3 | 8,89 | 811 | 0,995 |
| przed ręczną redukcją | II/3 | 8,76 | 802 | 0,983 |
| ręczna redukcja | II/3 → II/2 | 7,76 | 826 | — |

Zapis diagnostyczny potwierdził również zdarzenie `GEAR_EVENT before=3 requested=2` przy ręcznej redukcji. Po zmianie na II/2 silnik zaczął odzyskiwać obroty i prędkość.

**Przyczyna.** Dotychczasowe zabezpieczenia miały dziurę między progami. Dla lekkiego zestawu (<3,175 t) blokada top gear przy load ≥0,70 wymagała RPM <2100; ogólna blokada load ≥0,80 wymagała RPM <1750. W punkcie decyzji 2126 rpm / 0,755 load / 2,577 t oba warunki przepuszczały. Predykcja top gear dawała około `2126 × 14.324 / 22.878 = 1331 rpm`, czyli powyżej dotychczasowego minimum 1200. W rzeczywistej zmianie traktor wytracił prędkość, więc obroty spadły znacznie niżej. GIANTS później zwracał 3 → 3 nawet przy bardzo wysokim obciążeniu i niskich obrotach. Nie istniał własny, niezależny failsafe wymuszający II/3 → II/2.

**Zastosowana poprawka.** P1: limit 15 km/h wyznacza II/2 jako sufit roboczy, a ogólny lugging recovery ma wymusić redukcję przy gazie ≥0,85, load ≥0,75 i RPM ≤1450. Po redukcji obowiązuje 2,5 s hold. Nie zastosowano samego podniesienia minimalnych RPM zmiany na II/3, które pogorszyłoby jazdę transportową.

**Status:** załatane — do testu. Sprawdzić, czy Brony pozostają na II/2 oraz czy przy innym ciężkim obciążeniu awaryjna redukcja zadziała bez huntingu.

### INC-004 — C-330M + U021/1: upshift ponad bieg roboczy

**Objaw.** Na II/1 pług pracuje prawidłowo, lecz automat wrzuca II/2, mimo że limit prędkości został już osiągnięty. Silnik przechodzi na zbyt niskie obroty.

**Źródło.** Ten sam wiarygodny log D2. Pług Grudziądz U021/1, limit 8,4 km/h.

| Etap | Bieg | km/h | RPM | load |
|---|---|---:|---:|---:|
| poprawna praca | II/1 | 8,35–8,39 | około 2030–2165 | około 0,47–0,55 |
| po upshiftcie | II/2 | około 8,3 | 1149 → 1105 → 1078 → 1064 → około 1040 | zmienne |

**Przyczyna.** Predykcja GIANTS może wybrać wyższy bieg przy osiągniętym limicie narzędzia, ponieważ optymalizuje również obroty i zużycie paliwa. Bazowy kontroler nie miał jawnego ograniczenia najwyższego biegu roboczego. To nie dowód na nieprawidłową moc C-330M: II/1 przy około 8,4 km/h odpowiada użytecznym obrotom, a II/2 przy tej samej prędkości około 1100 rpm.

**Zastosowana poprawka.** P1: najwyższy bieg spełniający minimum 1500 rpm przy aktywnym limicie, blokada upshiftu ponad wyliczony sufit i redukcja do właściwego biegu po opuszczeniu narzędzia. U021/1 powinien wybrać II/1.

**Status:** załatane — do testu. Potwierdzić zachowanie przy 8,4 km/h i podczas podnoszenia oraz opuszczania narzędzia.

### INC-005 — ograniczenie prędkości narzędzia i pułapka masy zestawu

**Obserwacja.** D2 potwierdził, że `vehicle:getSpeedLimit(true)` zwraca aktywny limit pracującego narzędzia: U021/1 8,4 km/h, U-201 13 km/h, Brony 5 15 km/h, a po podniesieniu narzędzia brak skończonego limitu (`inf`). Dzięki temu nie trzeba rozpoznawać nazw ani typów maszyn.

**Wniosek.** Masa jest użyteczna do doboru biegu startowego i ostrożności zestawu, ale nie jest miarą oporu pracy w glebie. Lekki pług może stawiać duży opór, a ciężka przyczepa na równej drodze nie musi oznaczać dużego chwilowego obciążenia. Próg 3,175 t nie może być jedyną ochroną przed zbyt wysokim biegiem.

**Zastosowana poprawka.** P1 rozdziela aktywny limit pracy od transportu oraz dodaje niezależną redukcję na podstawie RPM, gazu i load. Brak skończonego limitu oznacza powrót do zwykłej strategii drogowej, a nie sztuczny limit 15 km/h.

**Status:** koncepcja wdrożona — do testu dla narzędzi z różnymi limitami i dla przyczep bez limitu roboczego.

## 4. Architektura skrzyni i uzasadnienie progów

### Bazowy kontroler

Plik `Scripts/C330TransmissionFix.lua`, SHA źródła D2 `e7d5be8315cb54d65de6a92f7ff9d9445353f8f8`. Obejmuje tylko konfigurację `c330m.xml` z własnego katalogu moda i silniki C-330/C-330M. Tryby manualne pozostawia GIANTS. W automacie wyłącza automatyczną optymalizację grup przez GIANTS i utrzymuje zamierzony porządek I/1 → I/2 → I/3 → II/1 → II/2 → II/3, z redukcją w odwrotnej kolejności.

Najważniejsze wartości bazowe: downshift zakresu 1500 rpm, load 0,75 lub gaz 0,85 przy load ≥0,55; II/1 → I/3 tylko przy prędkości ≤6,0 km/h; reset zakresu przy ≤0,5 km/h; lekkie zestawy <3,175 t mogą zaczynać na I/3 lub R-II; range up 2050 rpm i load ≤0,55, stabilizacja 800 ms; dwell upshiftu 2000 ms; cooldown zakresu 800 ms; recovery hold 2500 ms. Top gear ma dodatkowe zabezpieczenia obciążenia i przewidywanych obrotów.

Te progi opisują stan wyjściowy, nie uniwersalne wartości fabryczne. Nie należy zmieniać ich zbiorczo w odpowiedzi na pojedynczy objaw. Dotychczasowe przełożenia i charakterystyki silnika pozostają punktami referencyjnymi.

### Warstwa P1

`Scripts/C330TransmissionWorkFix.lua` jest osobną warstwą gameplay nakładaną po bazowym kontrolerze. Jej zadaniem jest ograniczenie błędnych decyzji roboczych i ratowanie silnika przy zbyt wysokim biegu. Diagnostyka D2 obserwuje finalną decyzję. Dodatkowe breadcrumbs: `WORK GEAR HOLD`, `WORK GEAR DOWN`, `WORK RANGE UP`, `LUG DOWNSHIFT`, `WORK RELEASE HOLD`, `BLOCK UPSHIFT HOLD`.

Minimum 1500 rpm przy limicie pracy to **próg strategii testowej**, nie wartość z fabrycznej instrukcji Ursusa. Dobór jest zależny od rzeczywistych prędkości obu wersji. Przykłady wyników: 8,4 km/h → II/1; 13–15 km/h → II/2; wolniejsze narzędzia mogą wymagać zakresu I. Sam limit nie gwarantuje dostępnej mocy — dlatego pozostaje osobny lugging failsafe.

### Diagnostyka i polityka wydań

`C330FullDiagnostic.lua` pozostaje we wszystkich prerelease na obecnym etapie. Pełne wydania usuwają go podczas budowania ZIP-a. Nie należy ponownie podłączać osobnego `FS25_ZZ_C330FullDiagnostic`, a tym bardziej przywracać synchronicznego logowania w hooku predykcji. Ochrona przed awarią diagnostyki jest obowiązkowa. Pliki dokumentacyjne i debugowe nie powinny trafiać do paczki gry; przy dodawaniu nowego katalogu z dokumentacją należy uwzględnić go w wykluczeniach workflow ZIP-a.

## 5. Rejestr otwartych problemów i ryzyk

| ID | Problem / ryzyko | Stan | Co trzeba potwierdzić |
|---|---|---|---|
| INC-001 | C-330M I/3 ogranicza orkę do około 6 km/h | P1 — do testu | I/3 → II/1 pod obciążeniem bez zbędnego podnoszenia pługa |
| INC-002 | D1 przerywa update i zalewa log | D2 — potwierdzona poprawa | Brak regresji diagnostyki w dalszych buildach |
| INC-003 | C-330 Brony 5, II/3 dusi silnik | P1 — do testu | II/2 jako sufit i skuteczna redukcja przy luggingu |
| INC-004 | C-330M U021/1, II/1 → II/2 przy 8,4 km/h | P1 — do testu | Utrzymanie II/1, poprawny powrót do transportu |
| INC-005 | Dobór biegu zależny od masy zamiast oporu | Strategia P1 — do testu | Różne narzędzia, przyczepy i obciążenia ADS |
| INC-006 | Hunting po awaryjnej redukcji | Ryzyko objęte hold 2,5 s | Brak sekwencji II/3 → II/2 → II/3 w krótkim czasie |
| INC-007 | Zbyt szybki upshift po podniesieniu maszyny | Hold 2,5 s — do testu | Poprawne zachowanie na nawrocie i ponowne opuszczenie |
| INC-008 | Manualne sterowanie i inne pojazdy | Ryzyko regresji | Brak wpływu na manual i ciągniki spoza własnego c330m.xml |
| INC-009 | Brak pełnego testu P1 w FS25 | Otwarte | Nowy log z obu wersji ciągnika i trzema klasami narzędzi |
| INC-010 | Dokumentacja włączona do ZIP-a gry | Do kontroli | Wykluczenie `spostrzezenia/` przy przyszłym buildzie |

## 6. Plan walidacji następnego prerelease

1. Uruchomić wyłącznie aktualną paczkę Ursusa; usunąć stary oddzielny mod diagnostyczny. Zachować kopię poprzedniego ZIP-a i save przed testami.
2. C-330 bez narzędzia: start, wszystkie biegi w automacie, możliwość osiągnięcia II/3 przy dostępnej mocy, hamowanie i redukcje. Sprawdzić, czy nie ma przeskoków zakresów oraz czy kamera/menu działają prawidłowo.
3. C-330 + Brony 5: opuszczone przy limicie 15 km/h, praca pod obciążeniem, podjazd, zjazd, podniesienie i ponowne opuszczenie. Oczekiwany sufit II/2. Wymusić warunki dużego obciążenia, aby sprawdzić failsafe.
4. C-330M + U021/1: praca przy 8,4 km/h, również pod górę. Potwierdzić I/3 → II/1 pod obciążeniem i blokadę II/1 → II/2, gdy narzędzie pracuje. Po podniesieniu sprawdzić 2,5 s hold i powrót do jazdy drogowej.
5. U-201 lub narzędzie około 13 km/h: oczekiwany II/2. Dodatkowo wolniejsze narzędzie, aby sprawdzić poprawny dobór zakresu I.
6. Jazda z przyczepą bez aktywnego limitu pracy: zweryfikować, czy governor nie narzuca sztucznego sufitu. Sprawdzić redukcję pod obciążeniem i brak huntingu.
7. Manualny tryb i inny pojazd: upewnić się, że warstwa Ursusa nie przechwytuje obcej skrzyni.
8. Zachować pełny `log.txt` wraz z datą, nazwą builda, listą aktywnych modów, modelem, konfiguracją kół/balastu, użytymi narzędziami i informacją, które zmiany wykonano ręcznie. Nie wystarczy sam wycinek z błędem.

Przy kolejnym logu porównywać `predCur`, `predResult`, aktualny/target gear, range, RPM, prędkość, loadSel, adsRaw, nativeRaw, speedLimitTools oraz timery dwell/hold/cooldown. Oddzielać żądanie kontrolera od rzeczywiście zakończonej zmiany mechanicznej. Jeśli wystąpi nowy błąd Lua, najpierw wyeliminować awarię instrumentacji; nie stroić silnika na podstawie zaburzonego update'u.

## 7. Odnośniki i ograniczenia archiwum

- Bazowy kontroler: https://github.com/StrielokPL/ursus330fs25/blob/main/Scripts/C330TransmissionFix.lua
- Warstwa robocza P1: https://github.com/StrielokPL/ursus330fs25/blob/main/Scripts/C330TransmissionWorkFix.lua
- Diagnostyka: https://github.com/StrielokPL/ursus330fs25/blob/main/Scripts/C330FullDiagnostic.lua
- Loader: https://github.com/StrielokPL/ursus330fs25/blob/main/Scripts/C330ShopOrder.lua
- Polityka pakowania: https://github.com/StrielokPL/ursus330fs25/blob/main/.github/workflows/release.yml
- Opis P1: https://github.com/StrielokPL/ursus330fs25/blob/main/.release/notes.md
- Historia D1: https://github.com/StrielokPL/ursus330fs25/commit/194c34a83d8f084f00deffa28a1961e1d9c0b937
- Historia D2: https://github.com/StrielokPL/ursus330fs25/commit/4e12fad3068a6598779e9c447ab345c6768d76cd
- Historia P1: https://github.com/StrielokPL/ursus330fs25/commit/3f4b2dd145eb3da2b78a296ff66530bf5a49bc10

Surowe logi użytkownika nie zostały automatycznie zapisane w repozytorium. Ten dokument zachowuje znane, wcześniej odczytane przykłady i wnioski, ale nie zastępuje pełnych plików źródłowych. Nie należy przypisywać mu niezweryfikowanych nazw plików, timestampów ani udawać, że wykonano test P1 po jego opublikowaniu. Przy późniejszej archiwizacji logów można dodać ich rzeczywiste nazwy i sumy SHA-256 oraz odnośniki do odpowiednich incydentów.


## 2026-09-07 — 0.0.5.1 P2

Log P1 potwierdził trzysekundowe oczekiwanie po zwróceniu niższego biegu oraz powtarzanie I/3 ↔ II/1. P2 zwalnia wyłącznie natywną blokadę kierunku dla potwierdzonej redukcji, dodaje ocenę rezerwy i pamięć nieudanej zmiany. Nie zmienia silnika ani kół. Dym korzysta opcjonalnie z ADS, z fallbackiem GIANTS. Diagnostyka obejmuje rzeczywiste zmiany, ich czas wykonania i poprawne API nacisku wszystkich kół; szczegóły w `docs/P2_DIAGNOSTICS.md`. Potwierdzono testy izolowane; jazda w FS25 pozostaje do wykonania.
