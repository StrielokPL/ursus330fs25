## Ursus C-330 / C-330M 0.0.4.3

**Shop cleanup / ordering test.** Physics from 0.0.4.2 is unchanged.

### Please verify in the shop
Expected top sequence: **Engine -> Wheels -> Water -> Front ballast -> Cabin -> Loader console**. After that, remaining selectors should be much closer to a front-to-rear customization flow.

Known structural limitation: rear metal wheel weights are still selectable inside **Wheels**, because their meshes and physical mass are wheel sub-configurations. They were not rewritten during this safe cleaning pass.

### Price cleanup
- Water: **free (0)**.
- Rear wheel ballast: **100 / 300 / 400 / 300** for +40 / +144 / +184 / alternate +144 kg.
- Front 42 kg ballast: **100**.
- Cabins: **500**.
- Loader console: **600**.

### Runtime cleanup
The temporary tyre diagnostic logger has been removed. Liquid ballast stays **+132 kg per rear wheel, spring 14 / damper 30**; dry tyres stay **12 / 22**.

Please send either a screenshot/list of the visible selector order plus a normal `log.txt`. The important log marker is `[C330SHOP] local C-330 shop order active`; if it is absent, the ordering hook did not identify the active ShopConfigScreen and we will adjust only that helper.
