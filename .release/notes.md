## Ursus C-330 / C-330M 0.0.5.2 P3

Prerelease izolujący crash P2. Wersja wewnętrzna: **0.0.5.2**; tag: **0.0.5.2P3**.

P2 z 7 września 2026 był niegrywalny: 1102 wyjątków `Lights.lua:1469 math.abs(nil)` w `Vehicle.update`, zamarznięty ciągnik i kamera. Skrzynia w tym logu nie zdążyła pracować.

### Co znika względem P2

- Usunięty `C330ExhaustBridge.lua` (hook `Vehicle.update`, `toggleEffects`, `setParticleIntensity`).
- Brak mostka ADS → ExhaustExtension. Dym wraca do zachowania GIANTS / ExhaustExtension bez ingerencji Ursusa.
- Diagnostyka `[EXHAUST]` zostaje, ale `extension` będzie `n/a` / `false`.

### Co zostaje z P2 (do weryfikacji w jeździe)

- Ta sama warstwa skrzyni: redukcja zdejmuje tylko veto kierunku, pamięć nieudanego biegu, rezerwa momentu, poślizg, ochrona obrotów.
- Flight recorder `[C330FULLDIAG]` co 250 ms.
- Silnik, przełożenia, masy, opony i balast bez zmian.

### Test w grze

1. Zainstaluj **tylko** ZIP z tej publikacji. Usuń paczkę P2.
2. Wejście do C-330, rozruch, światła, kierunkowskazy, kamera — **nie może być czerwonego `Lights.lua`**.
3. Krótka jazda bez narzędzia, potem U021/1 jak w logu P2.
4. Jeśli bez mostka ciągnik jeździ, dopiero wtedy oceniamy biegi P2.
5. Prześlij pełny `log.txt`.
