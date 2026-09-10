## 0.0.5.1 — pełne wydanie — 2026-09-10

Pełne wydanie mechaniki sprawdzonej w P5 dla C-330 i C-330M.

- Naprawiony kontrakt `VehicleMotor.updateGear`: zachowane oba wyniki — gaz i hamulec. Usuwa źródło regresji P2/P3 prowadzącej do `Lights.lua:1469 abs(nil)`.
- Kontrola obrotów, zapasu momentu, poślizgu i stabilizacji przed automatyczną zmianą w górę, również w jeździe bez narzędzia.
- Redukcja przy przeciążeniu oraz warunkowe ponawianie nieudanego wyższego biegu; zachowana ochrona podczas pracy.
- Brak rejestratora diagnostycznego, jego automatycznego loadera i komunikatu startowego WorkFix w paczce. Usunięte puste wywołania logujące bazowego sterownika. Narzędzie diagnostyczne zachowane wyłącznie w `debug/` repozytorium do testów.
- Brak mostka ADS–dym. Integracja odczytu obciążenia ADS pozostaje opcjonalna, z fallbackiem GIANTS.
- Uaktualnione README, status walidacji i lista dalszych testów.

### Walidacja i ograniczenia

P5, FS25 1.23.1.0, log `log(20260910-191745).txt`: 0 wpisów `Error:`, C-330 22,887 km/h, C-330M 26,289 km/h, oba osiągnęły II3. Bronowanie: II1, około 7,4 / 8,5 km/h. To test bazowej mechaniki P5; finalna paczka po usunięciu diagnostyki wymaga krótkiego sprawdzenia w grze. Testy automatyczne nie symulują FS25.

Multiplayer aktualnego sterownika nie jest jeszcze zweryfikowany. Prognoza obciążenia II1 → II2 wymaga porównania z rzeczywistą próbą pod obciążeniem. Powrót po zapisanej porażce biegu ma test regresyjny, ale najnowszy przejazd nie uruchomił tej ścieżki.

### Instalacja

Pobierz `FS25_UrsusC330_330M_4x2.zip`, podmień poprzednią paczkę w katalogu mods. Nie rozpakowuj i nie zmieniaj nazwy ZIP. W grze wersja pozostaje `0.0.5.1`; pełne wydanie od P5 odróżnia tag wydania i brak diagnostyki. Nie używaj archiwum „Source code” jako moda.
