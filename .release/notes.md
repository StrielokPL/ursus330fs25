## Ursus C-330 / C-330M 0.0.5.1 P4

Wersja testowa naprawiająca regresję P2/P3: `Lights.lua:1469: invalid argument #1 to abs (number expected, got nil)`.
Wersja wewnętrzna: **0.0.5.1**, tag: **0.0.5.1P4**.

### Poprawki

- `C330TransmissionWorkFix` oraz `C330FullDiagnostic` przekazują oba wyniki `VehicleMotor.updateGear`: skorygowany gaz i hamulec. Każda z obu nakładek wcześniej odrzucała hamulec.
- Przywrócony kompletny rejestrator diagnostyczny po uciętym pliku z nieukończonej próby P4. W logu identyfikuje się jako P4.
- Mostek efektów dymu pozostaje wyłączony; nie instalujemy nakładki na `Vehicle.update` ani sterowania `toggleEffects` / `setParticleIntensity`.
- Testy obejmują oba wyniki, hamulec 0 / częściowy / pełny, automat, manual, cofanie, klienta oraz inne pojazdy, z diagnostyką i bez niej.

### Zakres weryfikacji

Testy Lua i XML oraz porównanie skryptów w paczce ze źródłami są częścią budowania wydania. Test izolowany nie zastępuje jazdy w FS25 ani próby multiplayer.
Silnik, przełożenia, masy, opony i reguły wyboru biegów z P2/P3 nie są przestrajane w tej poprawce.

### Test w grze

1. Zastąp dotychczasowy plik `FS25_UrsusC330_330M_4x2.zip` paczką z tego wydania i uruchom grę ponownie.
2. Sprawdź C-330 i C-330M: ruszanie, hamowanie, światła STOP, zmianę kierunku oraz skrzynię ręczną i automatyczną.
3. Sprawdź jazdę z narzędziem i redukcję pod obciążeniem. W logu powinien działać `[C330FULLDIAG]` w wersji P4, bez błędu `Lights.lua:1469`.
4. Zachowaj pełny `log.txt` z testu.
