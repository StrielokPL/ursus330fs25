# Validation status — Ursus C-330 / C-330M 0.0.4.3

## Status wydania

**Singleplayer / kariera: STABLE**

Aktualny rebuild 0.0.4.3 został przetestowany w normalnej karierze oraz w kontrolowanych testach fizyki i konfiguracji. Ostatni pełny log testowy nie zawiera błędów Lua, call stacków ani błędów przypisanych do C-330.

**Multiplayer aktualnego rebuildu: NOT YET VALIDATED**

Aktualna wersja 0.0.4.3 nie przeszła jeszcze kompletnego testu host + drugi klient / dedicated server po wszystkich zmianach skrzyni, masy, opon, płynnego balastu i konfiguratora. Nie należy opisywać tego buildu jako „MP tested” tylko na podstawie historycznych testów wcześniejszego fixa dirty flagów.

## Ostatni zweryfikowany snapshot

Środowisko:

- Farming Simulator 25 **1.21.1.0**,
- Ursus C-330/C-330M **0.0.4.3**,
- normalny save kariery,
- sklep/warsztat, jazda bez obciążenia i z zestawami, testowa górka, zmiana ciśnienia i konfiguracji.

Aktywne mody skryptowe / fizyczne w ostatnim logu:

| Mod | Wersja | Znaczenie dla testu |
| --- | --- | --- |
| Advanced Damage System | 0.9.2.4 | źródło opcjonalnego `dynamicMotorLoad`; C-330 używa go read-only i ma fallback GIANTS |
| MudSystemPhysics | 1.3.1.0 | ciśnienie / fizyka opon; testy 1.00 i 2.40 bar |
| Mud Sprayer | 1.0.0.0 | współpracuje z systemem błota/pojazdów |
| tireSound | 1.0.0.0 | dodatkowa konfiguracja / dźwięk opon |
| toggleSuperStrength | 1.1.0.0 | aktywny w sesji; brak konfliktu z C-330 |
| Vehicle Years | 1.0.0.6 | aktywny w sesji; brak konfliktu z C-330 |

AIASF nie był aktywnym modem w tym konkretnym ostatnim snapshotcie. Jego testy dotyczą wcześniejszej diagnozy dirty flagów i są opisane osobno poniżej.

## Zweryfikowane punkty bezpieczeństwa

### Skrzynia C-330

- fabryczna wirtualna sekwencja 6F/2R: `I/1 -> I/2 -> I/3 -> II/1 -> II/2 -> II/3`,
- 2 s minimalnego dwell przed automatycznym upshiftem,
- mass-aware start: lekki zestaw może startować z I/3 / R-II, ciężki zachowuje niski zakres,
- kontrolowany `II/1 -> I/3` pod obciążeniem,
- ochrona `II/2 -> II/3` przed zbyt niskim RPM i wysokim obciążeniem,
- ADS jest opcjonalny i wyłącznie read-only.

Nietypowe przejście zakresu przy bardzo małej prędkości zaobserwowane w ostatnim teście zostało zreprodukowane podczas ekstremalnej próby wciągnięcia naczepy na testową górkę. Duży uślizg kół oraz geometria zestawu chwilowo odciążały / unosiły napędzaną tylną oś. W normalnym użytkowaniu nie zaobserwowano anomalii skrzyni; zdarzenie nie jest traktowane jako regresja sterownika.

### Masa i fabryczny balast

- masa bazowa gotowego do pracy C-330: **1675 kg**,
- rozkład bazowy około **38% przód / 62% tył**,
- przedni fabryczny balast: **42 kg**,
- tylne metalowe warianty: **40 / 144 / 184 kg**,
- pełny fabryczny metalowy balast: **226 kg**, około **1901 kg** całkowitej masy.

### Opony suche

- spring **12**,
- damper **22**,
- `suspTravel=0.07`,
- wartości wybrane po kontrolowanych porównaniach A/B,
- MudSystemPhysics pozostaje właścicielem warstwy ciśnienia/radius/friction.

### Płynny balast tylnych opon

- **+132 kg na każde tylne koło**,
- **+264 kg łącznie**,
- filled-tyre spring około **14**,
- filled-tyre damper około **30**,
- konfiguracja jest niezależna od metalowych obciążników kół,
- podczas przebudowy preview w sklepie nie zaobserwowano kumulowania `additionalMass`.

### Sklep

Zweryfikowany początek kolejności:

`Engine -> Wheels -> Water -> Front ballast -> Cabin -> Loader console`

Hook sortowania jest ograniczony do `c330m.xml` i nie zmienia globalnych priorytetów konfiguracji GIANTS dla innych pojazdów.

## Historyczny fix dirty flagów / geneza AIASF

Źródłowa paczka użyta do obecnego rebuildu **już zawierała** wcześniejszy fix `Static Cabins`; nie był nakładany ponownie podczas prac w `ursus330fs25`.

Oryginalna C-330 zużywała niemal cały 32-bitowy budżet dirty flagów. Wysokie bity zaczęły być współdzielone przez kilka systemów, w tym `AIAutomaticSteering`, `AttacherJoints`, `MoveableMirrors`, system brudu oraz dirty flagi Advanced Damage System. ADS mógł w efekcie podnieść bit interpretowany równocześnie jako Automatic Steering i doprowadzić w multiplayer do błędu `writeSegmentStatesToStream` przy `steeringFieldCourse == nil`.

Naprawa `Static Cabins`:

- usunęła 18 zbędnych kabinowych `movingTool`,
- usunęła odpowiadające im wpisy Interactive Control i animacje,
- zachowała kabiny jako statyczną geometrię,
- odzyskała 18 dirty flagów.

To dochodzenie doprowadziło do powstania AI Automatic Steering Fix (AIASF):
https://github.com/StrielokPL/Farming25fixnmix

Historyczny test fixa dirty flagów z ADS 0.9.2.4 i diagnostycznym AIASF był pomyślny, ale **nie zastępuje przyszłego testu multiplayer aktualnego rebuildu 0.0.4.3**.

## Co zostało do walidacji multiplayer

Przed zmianą statusu na MP-stable należy wykonać co najmniej:

1. host + drugi klient,
2. zakup nowego C-330 przez hosta i klienta,
3. zmiana koła / woda / balast / kabina / silnik w warsztacie,
4. jazda i zmiany kierunku na automacie,
5. zestaw lekki i ciężki,
6. zapis/reload serwera,
7. ponowne dołączenie klienta,
8. reset i sprzedaż/usunięcie pojazdu,
9. kontrola `readStream`, `writeStream`, `readUpdateStream`, `writeUpdateStream` i dirty flagów.

Do tego czasu oficjalny status pozostaje: **stable singleplayer career / multiplayer not yet validated**.
