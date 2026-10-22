using UnityEditor;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem.UI;
#endif

namespace Cats.EditorTools
{
    /// <summary>Builds uGUI elements in code with the game's look (warm text, dark translucent panels).</summary>
    public static class UIFactory
    {
        public static readonly Color Warm = new Color(1f, 0.78f, 0.5f);
        public static readonly Color Cream = new Color(1f, 0.95f, 0.86f);
        public static readonly Color PanelColor = new Color(0.03f, 0.04f, 0.09f, 0.68f);

        public static Font Title => AssetDatabase.LoadAssetAtPath<Font>(CatsPaths.Root + "/Art/Fonts/Lobster-Regular.ttf") ?? Body;
        public static Font Body => AssetDatabase.LoadAssetAtPath<Font>(CatsPaths.Root + "/Art/Fonts/Nunito.ttf") ??
                                   Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        public static Sprite Sprite(string name) => AssetDatabase.LoadAssetAtPath<Sprite>($"{CatsPaths.Textures}/{name}.png");

        public static void EventSystem()
        {
            var es = new GameObject("EventSystem");
            es.AddComponent<EventSystem>();
#if ENABLE_INPUT_SYSTEM
            es.AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
#else
            es.AddComponent<StandaloneInputModule>();
#endif
        }

        public static Canvas Canvas(string name, int order = 0)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var canvas = go.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = order;
            var scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 1f;
            go.AddComponent<GraphicRaycaster>();
            return canvas;
        }

        public static RectTransform Rect(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        public static RectTransform Stretch(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            return rt;
        }

        public static Image Img(RectTransform rt, string sprite, Color color, bool raycast)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = sprite != null ? Sprite(sprite) : null;
            img.color = color;
            img.raycastTarget = raycast;
            return img;
        }

        public static Text Label(RectTransform rt, int size, TextAnchor align, Color color, Font font = null)
        {
            var t = rt.gameObject.AddComponent<Text>();
            t.font = font ?? Body;
            t.fontSize = size;
            t.alignment = align;
            t.color = color;
            t.raycastTarget = false;
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            return t;
        }

        public static void Shadow(Graphic g, float alpha = 0.7f, float dist = 3f)
        {
            var s = g.gameObject.AddComponent<Shadow>();
            s.effectColor = new Color(0f, 0f, 0f, alpha);
            s.effectDistance = new Vector2(dist, -dist);
        }

        public static Button Button(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, string text, out Text label, int fontSize = 44)
        {
            var rt = Rect(name, parent, anchor, pos, size);
            var img = Img(rt, "UI_Panel", PanelColor, true);
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            var c = ColorBlock.defaultColorBlock;
            c.normalColor = Color.white;
            c.highlightedColor = new Color(1.25f, 1.1f, 0.9f);
            c.pressedColor = new Color(1.6f, 1.25f, 0.8f);
            c.selectedColor = Color.white;
            c.colorMultiplier = 1.5f;
            c.fadeDuration = 0.08f;
            b.colors = c;
            var tr = Stretch("Text", rt);
            tr.offsetMin = new Vector2(30, 0);
            tr.offsetMax = new Vector2(-30, 0);
            label = Label(tr, fontSize, TextAnchor.MiddleLeft, Cream);
            label.text = text;
            return b;
        }

        public static Button Button(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, string text, int fontSize = 44)
            => Button(name, parent, anchor, pos, size, text, out _, fontSize);

        public static Slider Slider(string name, Transform parent, Vector2 anchor, Vector2 pos, float width, string caption, float min, float max)
        {
            var root = Rect(name, parent, anchor, pos, new Vector2(width, 110));
            var cap = Rect("Caption", root, new Vector2(0.5f, 1f), new Vector2(0, -22), new Vector2(width, 44));
            Label(cap, 36, TextAnchor.MiddleLeft, Cream).text = caption;
            var bar = Rect("Slider", root, new Vector2(0.5f, 0f), new Vector2(0, 30), new Vector2(width, 44));
            var s = bar.gameObject.AddComponent<Slider>();
            var bg = Stretch("Background", bar);
            bg.anchorMin = new Vector2(0, 0.35f);
            bg.anchorMax = new Vector2(1, 0.65f);
            Img(bg, "UI_Panel", new Color(1f, 1f, 1f, 0.18f), true);
            var fillArea = Stretch("Fill Area", bar);
            fillArea.anchorMin = new Vector2(0, 0.35f);
            fillArea.anchorMax = new Vector2(1, 0.65f);
            fillArea.offsetMin = new Vector2(8, 0);
            fillArea.offsetMax = new Vector2(-8, 0);
            var fill = Stretch("Fill", fillArea);
            Img(fill, "UI_Panel", Warm, false);
            var handleArea = Stretch("Handle Slide Area", bar);
            handleArea.offsetMin = new Vector2(20, 0);
            handleArea.offsetMax = new Vector2(-20, 0);
            var handle = Rect("Handle", handleArea, new Vector2(0, 0.5f), Vector2.zero, new Vector2(52, 52));
            var hImg = Img(handle, "UI_JoystickKnob", Color.white, true);
            s.fillRect = fill;
            s.handleRect = handle;
            s.targetGraphic = hImg;
            s.direction = UnityEngine.UI.Slider.Direction.LeftToRight;
            s.minValue = min;
            s.maxValue = max;
            return s;
        }

        /// <summary>Volumes, quality, camera sensitivity and inversion. Hidden by default.</summary>
        public static SettingsPanel Settings(Transform parent)
        {
            var panel = Rect("Settings", parent, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1000, 900));
            Img(panel, "UI_Panel", new Color(0.03f, 0.04f, 0.09f, 0.88f), true);
            var title = Rect("Title", panel, new Vector2(0.5f, 1f), new Vector2(0, -70), new Vector2(900, 100));
            var tt = Label(title, 72, TextAnchor.MiddleCenter, Warm, Title);
            tt.text = "Настройки";
            Shadow(tt);
            var sp = panel.gameObject.AddComponent<SettingsPanel>();
            sp.music = Slider("Music", panel, new Vector2(0.5f, 1f), new Vector2(0, -200), 820, "Музыка и атмосфера", 0f, 1f);
            sp.sfx = Slider("Sfx", panel, new Vector2(0.5f, 1f), new Vector2(0, -320), 820, "Звуки", 0f, 1f);
            sp.sensitivity = Slider("Sensitivity", panel, new Vector2(0.5f, 1f), new Vector2(0, -440), 820, "Чувствительность камеры", 0.3f, 2f);
            sp.qualityButton = Button("Quality", panel, new Vector2(0.5f, 1f), new Vector2(0, -560), new Vector2(820, 90), "Качество", out sp.qualityLabel, 38);
            sp.invertButton = Button("Invert", panel, new Vector2(0.5f, 1f), new Vector2(0, -665), new Vector2(820, 90), "Камера", out sp.invertLabel, 38);
            sp.backButton = Button("Back", panel, new Vector2(0.5f, 0f), new Vector2(0, 80), new Vector2(420, 96), "Готово", out var bl, 42);
            bl.alignment = TextAnchor.MiddleCenter;
            panel.gameObject.SetActive(false);
            return sp;
        }

        public static CanvasGroup Fade(Transform parent)
        {
            var fade = Stretch("Fade", parent);
            Img(fade, null, Color.black, false);
            var g = fade.gameObject.AddComponent<CanvasGroup>();
            g.blocksRaycasts = false;
            g.interactable = false;
            g.alpha = 1f;
            return g;
        }
    }
}
