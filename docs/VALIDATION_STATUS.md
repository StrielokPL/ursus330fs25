# Walidacja 0.0.5.1 — 2026-09-10

## Dowody

Bazą pełnego wydania jest P5 (`4308ac90bcbf77a72340a7b03d795c26fde615d4`). Finalizacja usuwa diagnostykę i puste wywołania logujące bez strojenia progów skrzyni.

| Próba | Wynik i granice |
| --- | --- |
| P4, log 20260910-172726 | Jazda na mokrym; wcześniejszy błąd Lights nie wystąpił. |
| P4, log 20260910-185005 | Suchy test obu ciągników; C330M nie odzyskał II3. Uzasadnienie poprawki P5. Lista aktywnych modów pochodziła z careerSavegame(1).xml. |
| P5, log 20260910-191745 | FS25 1.23.1.0; nowo zakupione C330 i C330M, kolejno deski i te same Brony 5. 0 wpisów Error:, 0 decyzji FAILED GEAR MEMORY. |
| C330 bez narzędzia, P5 | II3; maksimum 22,887 km/h. |
| C330M bez narzędzia, P5 | II3; maksimum 26,289 km/h. Po redukcji ponownie II2 i II3. |
| C330 z bronami, 21:14:50–21:14:53 | II1, mediana 7,406 km/h; przewidywane obciążenie II2 1,122. |
| C330M z bronami, 21:17:04–21:17:11 | II1, mediana 8,479 km/h; przewidywane obciążenie II2 1,238. |
| Izolowane regresje Lua | Oba wyniki updateGear, redukcje, gotowość do upshiftu, odzyskanie biegu, ochrona pracy i separacja motorów; nie symulują fizyki gry. |

Prognozowane obciążenie to heurystyka sterownika, nie zmierzona praca na wyższym biegu. Brak Error: nie oznacza braku wszystkich ostrzeżeń innych modów. Lista modów dostępnych w logu nie jest równoznaczna z listą aktywnych.

## Pozostałe obszary — kolejność

1. **Multiplayer:** host i klient, następnie serwer dedykowany; oba modele, zakup, warsztat, jazda, kierunek, ciężki zestaw, zapis/wczytanie, ponowne dołączenie, reset i sprzedaż. Sprawdzić synchronizację biegów i dirty flagi. Aktualny sterownik nie ma statusu MP-tested.
2. **Rzeczywisty zapas II1 → II2:** kontrolowana próba na tym samym polu i z tym samym narzędziem, z pomiarem obrotów/prędkości po zmianie. Nie luzować ochrony wyłącznie na podstawie bieżącego obciążenia II1.
3. **Pamięć nieudanej zmiany:** celowo wywołać nieudaną zmianę, następnie poprawić warunki bez odpinania narzędzia/resetu stanu. P5 potwierdziło odzyskanie prędkości drogowej, ale nie uruchomiło FAILED GEAR MEMORY; ścieżka ma tylko izolowany test regresyjny.
4. **Warunki i kompatybilność:** ciężka przyczepa/podjazd, mokra gleba, różne ciśnienia i balast; porównać ADS włączony/wyłączony, zużyty silnik i zmianę konfiguracji C330 ↔ C330M. Wcześniejsze próby nie pokrywają całej macierzy P5.
5. **Tryby sterowania:** manual/półautomat, rewers, tempomat i pracownik AI; testy izolowane kontraktu nie zastępują jazdy w tych trybach.
6. **Finalna paczka:** krótka jazda po usunięciu diagnostyki, hamowanie/rewers, zapis i ponowne wczytanie. Nie wykonano nowej sesji gry po finalizacji.

WOM, hydraulika, zużycie paliwa i pełna kalibracja fizyczna C330M pozostają osobnymi obszarami realizmu; obecne testy skrzyni ich nie potwierdzają. Historyczny fix Static Cabins i wcześniejsza walidacja masy/ballastu pozostają zachowane, bez deklarowania nowego pełnego testu tych układów.
