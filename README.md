# Ursus C-330 / C-330M — Farming Simulator 25

**Pełne wydanie [0.0.5.1](https://github.com/StrielokPL/ursus330fs25/releases/tag/0.0.5.1).**

Autorzy: **StrielokPL**, Speedy, Miziuu.

[Pobierz ZIP moda](https://github.com/StrielokPL/ursus330fs25/releases/download/0.0.5.1/FS25_UrsusC330_330M_4x2.zip). Podmień poprzedni plik w mods, zachowując nazwę i postać ZIP. Archiwum „Source code” zawiera materiały rozwojowe i nie jest paczką instalacyjną.

## Stan mechaniki

- Automatyczna sekwencja 6F/2R; kontrola zakresów, obrotów i obciążenia dla C-330 oraz C-330M.
- Prędkości nominalne II3: 22,878 i 26,290 km/h przy 2200 obr./min.
- Dobór biegu uwzględnia aktywny limit narzędzia, zapas momentu, poślizg i stabilność prędkości. Limit narzędzia wyznacza sufit biegu, nie gwarantuje osiągnięcia prędkości roboczej.
- Opcjonalny odczyt obciążenia ADS z fallbackiem GIANTS. Mostek ADS–dym usunięty; efekty dymu nie są częścią tej integracji.
- Zachowane masa, balast, zawieszenie i statyczne kabiny wcześniejszego rebuildu. Podstawowa masa C-330 1675 kg; płynny balast tylnych opon +264 kg.
- Pełna paczka nie ładuje rejestratora diagnostycznego i nie generuje jego cyklicznych wpisów.

## Walidacja

Mechanika P5 została sprawdzona w singleplayer na FS25 1.23.1.0: osobne C-330 i C-330M, deski i te same brony, sucha gleba. Oba osiągnęły II3; log nie zawierał wpisów `Error:`. Finalne czyszczenie diagnostyki sprawdzane jest testami automatycznymi, a nie nową sesją gry. Multiplayer bieżącego sterownika pozostaje niewalidowany.

- [Status i dalsze testy](docs/VALIDATION_STATUS.md)
- [Historia zmian](CHANGELOG.md)
- [Dane bazowe i wcześniejsze strojenie](docs/FS25_C330_TECHNICAL_BASELINE.md)
- [Historyczna diagnostyka P2–P5](docs/P2_DIAGNOSTICS.md)

## Rozwój

`lua tests/regression.lua .` sprawdza izolowany kontrakt GIANTS, obie wartości zwracane przez updateGear i decyzje skrzyni. `python3 tests/package_check.py --source-only` sprawdza manifest i XML. Workflow dodatkowo sprawdza zawartość oraz integralność ZIP przed publikacją.

Rejestrator z P5 znajduje się w `debug/C330FullDiagnostic.lua`; służy regresjom i wydaniom testowym. Foldery debug, tests i docs nie trafiają do ZIP. Stan wewnętrzny sterownika potrzebny do decyzji, histerezy i pamięci błędnych zmian pozostaje w kodzie.

Historyczny fix Static Cabins odzyskał 18 dirty flagów przez usunięcie ruchomych elementów kabin. Kabiny pozostają statyczną geometrią. Wcześniejszy test tego fixa w MP nie zastępuje walidacji bieżącego sterownika; geneza: [AI Automatic Steering Fix](https://github.com/StrielokPL/Farming25fixnmix).
