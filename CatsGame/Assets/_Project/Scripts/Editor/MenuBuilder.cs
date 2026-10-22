using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.UI;
using UnityEngine.Video;

namespace Cats.EditorTools
{
    /// <summary>
    /// Builds Scenes/MainMenu.unity: the living photo of the reference picture (looping video),
    /// title, Continue / New game / Settings / About / Quit, menu music.
    /// </summary>
    public static class MenuBuilder
    {
        const string MenuArt = CatsPaths.Root + "/Art/Menu";

        public static void Build()
        {
            EditorUtil.EnsureFolder(CatsPaths.Scenes);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = Color.black;
            cam.cullingMask = 0;
            camGo.AddComponent<AudioListener>();
            cam.GetUniversalAdditionalCameraData().renderPostProcessing = false;

            // looping living photo
            var rtPath = MenuArt + "/MenuVideo.renderTexture";
            var rt = AssetDatabase.LoadAssetAtPath<RenderTexture>(rtPath);
            if (rt == null)
            {
                rt = new RenderTexture(1280, 720, 0, RenderTextureFormat.ARGB32) { name = "MenuVideo" };
                AssetDatabase.CreateAsset(rt, rtPath);
            }
            var videoGo = new GameObject("MenuVideo");
            var vp = videoGo.AddComponent<VideoPlayer>();
            vp.clip = AssetDatabase.LoadAssetAtPath<VideoClip>(MenuArt + "/menu_loop.mp4");
            vp.renderMode = VideoRenderMode.RenderTexture;
            vp.targetTexture = rt;
            vp.isLooping = true;
            vp.playOnAwake = false;
            vp.waitForFirstFrame = true;
            vp.skipOnDrop = true;
            vp.audioOutputMode = VideoAudioOutputMode.None;

            UIFactory.EventSystem();
            var canvas = UIFactory.Canvas("MenuUI");
            var root = canvas.transform;

            var bg = UIFactory.Rect("Background", root, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1920, 1080));
            var raw = bg.gameObject.AddComponent<RawImage>();
            raw.raycastTarget = false;
            var poster = AssetDatabase.LoadAssetAtPath<Texture2D>(MenuArt + "/menu_poster.jpg");
            raw.texture = poster;
            var fit = bg.gameObject.AddComponent<AspectRatioFitter>();
            fit.aspectMode = AspectRatioFitter.AspectMode.EnvelopeParent;
            fit.aspectRatio = 16f / 9f;

            var shade = UIFactory.Stretch("Shade", root);
            shade.anchorMax = new Vector2(0.45f, 1f);
            UIFactory.Img(shade, "UI_GradientLeft", Color.white, false);

            var title = UIFactory.Rect("Title", root, new Vector2(0f, 1f), new Vector2(610, -125), new Vector2(1100, 170));
            var tt = UIFactory.Label(title, 120, TextAnchor.MiddleLeft, UIFactory.Warm, UIFactory.Title);
            tt.text = "Лунная улица";
            UIFactory.Shadow(tt, 0.8f, 5f);
            var sub = UIFactory.Rect("Subtitle", root, new Vector2(0f, 1f), new Vector2(614, -238), new Vector2(1100, 56));
            var st = UIFactory.Label(sub, 38, TextAnchor.MiddleLeft, UIFactory.Cream);
            st.text = "ночная прогулка одного кота";
            UIFactory.Shadow(st);

            var menu = UIFactory.Stretch("MainPanel", root);
            var mm = canvas.gameObject.AddComponent<MainMenu>();
            Vector2 left = new Vector2(0f, 0.5f);
            Button MenuButton(string n, float y, string text, out Text label)
                => UIFactory.Button(n, menu, left, new Vector2(320, y), new Vector2(520, 88), text, out label, 40);
            mm.continueButton = MenuButton("Continue", 60, "Продолжить", out mm.continueLabel);
            mm.newGameButton = MenuButton("NewGame", -45, "Новая прогулка", out _);
            mm.settingsButton = MenuButton("Settings", -150, "Настройки", out _);
            mm.aboutButton = MenuButton("About", -255, "Об игре", out _);
            mm.quitButton = MenuButton("Quit", -360, "Выход", out _);
            var rec = UIFactory.Rect("Record", menu, new Vector2(0f, 0f), new Vector2(460, 50), new Vector2(800, 50));
            mm.recordText = UIFactory.Label(rec, 30, TextAnchor.MiddleLeft, UIFactory.Warm);
            mm.mainPanel = menu.gameObject;

            mm.settings = UIFactory.Settings(root);

            var about = UIFactory.Rect("About", root, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1200, 760));
            UIFactory.Img(about, "UI_Panel", new Color(0.03f, 0.04f, 0.09f, 0.88f), true);
            var at = UIFactory.Rect("Title", about, new Vector2(0.5f, 1f), new Vector2(0, -80), new Vector2(1100, 110));
            var att = UIFactory.Label(at, 80, TextAnchor.MiddleCenter, UIFactory.Warm, UIFactory.Title);
            att.text = "Лунная улица";
            var body = UIFactory.Stretch("Text", about);
            body.offsetMin = new Vector2(70, 170);
            body.offsetMax = new Vector2(-70, -160);
            UIFactory.Label(body, 36, TextAnchor.UpperLeft, UIFactory.Cream).text =
                "Ночь после дождя. Бенгальский кот выходит на мокрую террасу, а внизу у причала " +
                "рыбаки разбирают ночной улов. Пройди по балконам, карнизам и гирлянде к морю.\n\n" +
                "Модели, текстуры, звуки и музыка созданы процедурно (Python, Blender).\n" +
                "Шрифты: Lobster и Nunito — SIL Open Font License.\nДвижок: Unity, Universal Render Pipeline.";
            mm.aboutBack = UIFactory.Button("Back", about, new Vector2(0.5f, 0f), new Vector2(0, 85), new Vector2(420, 96), "Назад", out var bl);
            bl.alignment = TextAnchor.MiddleCenter;
            mm.aboutPanel = about.gameObject;
            about.gameObject.SetActive(false);

            var loading = UIFactory.Rect("Loading", root, new Vector2(1f, 0f), new Vector2(-420, 80), new Vector2(760, 70));
            mm.loadingText = UIFactory.Label(loading, 40, TextAnchor.MiddleRight, UIFactory.Cream);
            mm.fade = UIFactory.Fade(root);
            loading.SetAsLastSibling();

            var ver = UIFactory.Rect("Version", root, new Vector2(1f, 1f), new Vector2(-170, -40), new Vector2(300, 40));
            UIFactory.Label(ver, 26, TextAnchor.MiddleRight, new Color(1f, 1f, 1f, 0.45f)).text = "прототип v0.3";

            // music: the café waltz drifting up from the harbour, and the sea
            AudioSource Loop(string clip, float volume)
            {
                var go = new GameObject("Menu_" + clip);
                var a = go.AddComponent<AudioSource>();
                a.clip = AssetDatabase.LoadAssetAtPath<AudioClip>($"{CatsPaths.Root}/Audio/{clip}.wav");
                a.loop = true;
                a.playOnAwake = true;
                a.volume = volume;
                go.AddComponent<AudioVolume>().category = AudioVolume.Category.Music;
                return a;
            }
            Loop("mus_cafe_waltz", 0.45f);
            Loop("amb_sea", 0.25f);
            Loop("amb_crickets", 0.15f);
            var ui = new GameObject("UIAudio").AddComponent<AudioSource>();

            mm.video = vp;
            mm.background = raw;
            mm.poster = poster;
            mm.videoTarget = rt;
            mm.uiAudio = ui;
            mm.tap = AssetDatabase.LoadAssetAtPath<AudioClip>(CatsPaths.Root + "/Audio/sfx_ui_tap.wav");
            mm.levelScene = System.IO.Path.GetFileNameWithoutExtension(CatsPaths.Level01Scene);

            EditorSceneManager.SaveScene(scene, CatsPaths.MainMenuScene);
            CatsMenu.UpdateBuildScenes();
            Debug.Log("[Cats] Main menu built: " + CatsPaths.MainMenuScene);
        }
    }
}
