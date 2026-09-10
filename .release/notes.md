## Ursus C-330 / C-330M 0.0.5.1 P5

Wersja testowa: **0.0.5.1P5**, wersja wewnętrzna **0.0.5.1**.

### Skrzynia
- Kontrola gotowości do zmiany obejmuje teraz również jazdę bez narzędzia: obroty, przewidywany moment, poślizg i prędkość. Dotyczy zmian w zakresie oraz I/3 → II/1.
- Pamięć nieudanego biegu dopuszcza ponowną próbę bez aktywnego limitu pracy, gdy prognoza daje co najmniej 1300 obr./min i maksymalnie 75% obciążenia. Wymagane jest minimum 5 sekund od porażki oraz 2 sekundy ciągłego spełniania warunków gotowości. Sam upływ czasu nie wystarcza.
- Przy pracy pozostaje wymóg poprawy obciążenia oraz dotychczasowy próg rezerwy momentu. Przełożenia, moc i masy nie są zmieniane.
- Zachowana naprawa P4: obie nakładki przekazują skorygowany gaz i hamulec.

### Usunięcie mostka dymu
- Usunięty nieaktywny C330ExhaustBridge.lua, wpis ładowania i diagnostyka EXHAUST/c330Smoke.
- Usunięte testy pustego mostka; kontrola paczki pilnuje braku jego pozostałości.
- Natywne efekty pojazdu i zewnętrzny Exhaust Extension nie są modyfikowane. Odczyt obciążenia ADS nadal służy skrzyni.

### Walidacja i jazda testowa
102 sprawdzenia regresji Lua, w tym odtworzenie niskoobrotowej próby II/3 i późniejszego odblokowania, zachowanie rezerwy podczas bronowania oraz oddzielna pamięć dwóch silników. Testy izolowane nie zastępują FS25.

Podmień ZIP i uruchom grę ponownie. Sprawdź osobno C-330 oraz C-330M: rozpędzanie bez narzędzia, jazdę po nierównościach i ponowne rozpędzanie po redukcji. Następnie wykonaj próbę z tymi samymi bronami. Zachowaj pełny log; skrypty zgłaszają P5.
