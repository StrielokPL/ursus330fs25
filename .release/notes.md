## Ursus C-330 / C-330M 0.0.5.1 P2

Prerelease z poprawkami skrzyni na podstawie logu P1 z 7 września 2026. Wersja wewnętrzna: **0.0.5.1**; tag i komunikat startowy: **0.0.5.1P2**.

### Skrzynia

- Redukcja ratunkowa zwalnia blokadę kierunku zmiany GIANTS. Zachowuje mechaniczne czasy zmiany biegu i sprzęgła; samo żądanie niższego biegu nie czeka już na trzysekundową blokadę.
- Redukcja ma pierwszeństwo przed blokowaniem zbyt wysokiego biegu roboczego. Ochrona przed nadmiernymi obrotami nadal może odroczyć redukcję.
- Dobór biegu uwzględnia szacowaną rezerwę momentu po zmianie, rzeczywisty skok przełożeń, trend prędkości, poślizg oraz 0,8 s stabilnych warunków. Prognoza jest heurystyką sterownika, nie nową symulacją silnika.
- Nieudana zmiana jest zapamiętywana przed rozłączeniem napędu. Ponowienie wymaga co najmniej 5 s oraz spadku obciążenia o 0,12 i odzyskania prędkości. Sam powrót wysokich obrotów nie wystarcza.
- Zachowano sufit biegu wynikający z limitu narzędzia; nie można go obejść zmianą zakresu w bazowym sterowniku.
- P2 dotyczy automatycznej jazdy do przodu C-330/C-330M. Nie zmienia przełożeń, krzywych silnika, mas, geometrii ani strojenia kół. Wspólny odczyt ADS akceptuje prawidłowe przeciążenie ponad 100% również w bazowym sterowniku.

### Opcjonalny bridge wydechu

Dym bazowy i efekt ExhaustExtension korzystają z obciążenia ADS, jeśli jest dostępne, lub GIANTS. Odczyt jest tylko do odczytu; bridge modyfikuje wyłącznie efekty wizualne tego ciągnika. Zachowuje sekwencję rozruchową ExhaustExtension i kolory efektów używane przez ADS. Żaden z modów ADS, ExhaustExtension, MudSystemPhysics ani Mud Sprayer nie jest wymagany. Bridge nie zmienia tarcia ani promieni kół sterowanych przez mody błota.

### Diagnostyka

- `[C330FULLDIAG][vN][SHIFT_ACTUAL]`: rzeczywiste zmiany aktywnego/celowego biegu i zakresu, numery sekwencji, chwila zdarzenia i wiek decyzji.
- `[CONTROL]`: blokada GIANTS przed zwolnieniem, timery sprzęgła/zakresu/kierunku, prognoza obrotów i obciążenia z wiekiem próbki, powód decyzji, pamięć nieudanego biegu i czas wykonania redukcji.
- `[WHEELS]`: wszystkie koła, nacisk przez `wheel.physics:getTireLoad()` w tonach, kontakt, poślizg GIANTS, prędkość kątowa, ugięcie i bieżący promień. Brak lokalnego pomiaru siły jest jawnie oznaczony jako `unavailable`, nie jako zero.
- `[EXHAUST]`: źródło i filtrowane obciążenie, aktywność bridge'a ExhaustExtension i intensywność.
- Pomiary co 250 ms, narzędzia co 1000 ms. Ograniczona kolejka zdarzeń raportuje przepełnienie. Formatowanie i zapis nadal odbywają się poza ścieżką skrzyni.

### Walidacja i test w grze

Testy Lua w modelu kontraktu GIANTS obejmują opóźnioną redukcję z P1, pamięć nieudanego zakresu, rezerwę II/2, poślizg, ochronę przed nadmiernymi obrotami, zakres C-330M, tryb ręczny, brak ADS, błędne próbki, wydech z/bez dodatków i diagnostykę. Workflow sprawdza składnię, testy i zawartość ZIP-a przed publikacją. **Nie jest to potwierdzenie z jazdy w FS25**; parametry selekcji wymagają testu terenowego.

1. Zainstaluj ZIP z tej publikacji jako jedyny aktywny egzemplarz Ursusa; nie dodawaj osobnej starej diagnostyki.
2. C-330: przejazd bez narzędzia, następnie U021/1, Brony 3/5 i U240 w tych samych warunkach co w P1. Uwzględnij ciężki fragment, wyjazd na lżejszy i podniesienie narzędzia.
3. Sprawdź, czy po nieudanej zmianie automat utrzymuje niższy bieg, a po spadku obciążenia podejmuje udaną próbę. II/2 nie jest obowiązkowym biegiem dla każdych bron.
4. Przy jednakowej prędkości porównaj dym podczas lekkiej i ciężkiej pracy. Wykonaj rozruch/zgaszenie. Powtórz krótko bez ADS i bez ExhaustExtension.
5. C-330M: analogiczny krótki test; P1 z 7 września obejmował tylko C-330.
6. Prześlij pełny `log.txt`, z zaznaczeniem fragmentu, w którym bieg nadal był nieprawidłowy.
