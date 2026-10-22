# CatsGame — Unity-проект

Unity 6 (6000.0 LTS или новее), Universal Render Pipeline, Android, горизонтальный экран.

## Первый запуск

1. Unity Hub → **Add project from disk** → выбрать папку `CatsGame`.
   Открыть в Unity 6 LTS с модулем **Android Build Support**.
2. Если Unity спросит про новый Input System и перезапуск — согласиться.
3. В меню **Cats**:
   - **0. Do everything (1-3)** — настраивает проект (Android, Linear, URP Low/High, слои),
     создаёт материалы и префабы, собирает сцену `Assets/_Project/Scenes/Level01_MoonStreet.unity`;
   - **4. Bake lighting** — запекает свет (лайтмапы, пробы). На средней видеокарте 5–15 минут;
   - **5. Open main menu** — открыть меню: игра стартует с него (Продолжить / Новая прогулка / Настройки).
4. **Play.** В редакторе: WASD — идти (Shift — бег), пробел — прыжок, M — мяу, правая кнопка мыши — камера.
   На телефоне: джойстик слева, прыжок справа, «мяу» рядом с прыжком, свайп по экрану — камера.
5. Сборка: **File → Build Profiles → Android → Build**.

Сцена целиком генерируется из `Assets/_Project/Data/level01.json`.
Ручные правки в сцене пропадут при следующем **Cats ▸ 3**. Расстановку правьте в
`tools/level/level01_layout.py` (или переносите правки туда).

## Что где

```
Assets/_Project/
  Art/Textures   65 текстур: PBR, небо, эффекты, UI (tools/textures/gen_textures.py)
  Art/Models     40 FBX-моделей из Blender (tools/blender/make_models.py)
  Audio/         25 звуков: атмосфера, музыка кафе, кот, голуби (tools/audio/gen_audio.py)
  Art/Materials  создаются из Data/materials.json (Cats ▸ 2)
  Data/          materials.json, level01.json (tools/level/*.py)
  Prefabs/Generated  префабы моделей с URP-материалами (Cats ▸ 2)
  Generated/     меши уровня (Cats ▸ 3)
  Settings/      URP_High / URP_Low, постобработка, настройки запекания
  Scripts/Runtime  кот, камера, управление, зоны, UI, менеджер уровня
  Scripts/Editor   сборка сцены, импорт, материалы, настройка проекта
```

## Ключевые скрипты

| Скрипт | Что делает |
|---|---|
| `CatController` | ходьба/бег, прыжок, прыжок точно на лапку, карниз, скольжение, канат-гирлянда, зацеп когтями, «осторожный шаг» у края |
| `CatAnimator` | процедурная анимация кота-заглушки (лапы, хвост, наклон на канате) |
| `CatCameraRig` | камера сзади-сверху как на референсе, свайп, автодоводка, коллизии, зоны камеры |
| `LocalCatInput` | сенсорный джойстик + кнопка, клавиатура/геймпад в редакторе |
| `GameManager` | затемнение на старте, чекпоинты, респаун, подсказки, финал. Игроки — списком, готово к кооперативу |
| `NpcCat` | серый кот Барон на балконе: смотрит на игрока и рассказывает цель |
| `Level01Builder` | собирает всю сцену из JSON |
| `MenuBuilder`, `MainMenu` | главное меню: «живое фото» референса (видео-петля), кнопки, музыка, переход в уровень |
| `SaveSystem`, `SettingsPanel` | сохранение на чекпоинтах (JSON в persistentDataPath), рекорды, громкость, качество, камера |
| `PlanarReflection`, `PuddleSurface`, `Cats/PuddleReflection.shader` | зеркальные отражения в лужах (только «красиво»/High) |
| `Level01Atmosphere` | ореолы, световые конусы, свет из окон, подтёки, облака, лунная дорожка, частицы, ветер, голуби, звук |
| `CatAudio`, `AmbientAudio` | шаги, мяу, мурчание; море, сверчки, ветер, колокол |

## Пересоздание ассетов (не обязательно)

Всё уже лежит в репозитории. Если меняются генераторы:

```bash
python3 tools/textures/gen_textures.py          # текстуры (numpy, pillow)
python3 tools/level/materials.py                # materials.json
python3 tools/level/level01_layout.py           # level01.json
python3 tools/audio/gen_audio.py                # звуки (numpy)
python  tools/menu/make_menu_video.py           # фон меню: оживлённый референс, menu_loop.mp4 (нужен ffmpeg)
pip install bpy==5.2.2                          # Blender как Python-модуль (Python 3.13)
python  tools/blender/make_models.py            # FBX-модели
python  tools/blender/render_level.py out.png   # предварительный рендер стартового кадра в Cycles
```

Проверка, что C# компилируется, без Unity:
`dotnet build tools/compilecheck -p:UnityDlls=<папка с UnityEngine.dll и UnityEditor.dll>`.

## Важно знать

- **Кот — временная модель**, собранная из частей и анимированная кодом. Для релиза нужна
  профессиональная модель бенгальской кошки со скелетом и анимациями. `CatController` от модели
  не зависит, её можно заменить без переделки управления.
- Окна, фонари, гирлянды светятся за счёт emission и запечённого света. Без шага
  **Cats ▸ 4. Bake lighting** сцена будет заметно темнее и площе.
- Low/High качество выбирается автоматически (`QualityTier`): флагманы получают 60 FPS, MSAA,
  мягкие тени; средние телефоны — 30 FPS и рендер в 0.75 разрешения с FSR.
