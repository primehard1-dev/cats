using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UI;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem.UI;
#endif

namespace Cats.EditorTools
{
    /// <summary>
    /// Builds Scenes/Level01_MoonStreet.unity from Data/level01.json:
    /// geometry, props, lights, probes, sky, fog, post-processing, background, gameplay, UI, player and camera.
    /// Re-run it any time the layout changes; the scene is regenerated from scratch.
    /// </summary>
    public static class Level01Builder
    {
        static LevelData L;
        static MeshFactory.Bundle _meshes;
        static readonly MeshFactory Mf = new MeshFactory();
        static int _playerLayer, _catOnlyLayer, _ignoreRaycastLayer;
        static Transform _geo, _props, _lights, _gameplay, _background, _probes;

        public static void Build()
        {
            var json = AssetDatabase.LoadAssetAtPath<TextAsset>(CatsPaths.Data + "/level01.json");
            if (json == null) { Debug.LogError("[Cats] Data/level01.json not found"); return; }
            L = JsonUtility.FromJson<LevelData>(json.text);
            if (PrefabFactory.Load("Cat_Hero") == null) PrefabFactory.BuildAll();

            _playerLayer = ProjectSetup.Layer(ProjectSetup.PlayerLayer);
            _catOnlyLayer = ProjectSetup.Layer(ProjectSetup.CatOnlyLayer);
            _ignoreRaycastLayer = LayerMask.NameToLayer("Ignore Raycast");

            EditorUtil.EnsureFolder(CatsPaths.Scenes);
            EditorUtil.EnsureFolder(CatsPaths.Generated);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            _meshes = new MeshFactory.Bundle(CatsPaths.Generated + "/Level01_Meshes.asset");

            _geo = new GameObject("Geometry").transform;
            _props = new GameObject("Props").transform;
            _lights = new GameObject("Lights").transform;
            _gameplay = new GameObject("Gameplay").transform;
            _background = new GameObject("Background").transform;
            _probes = new GameObject("Probes").transform;

            BuildEnvironment(out var moon);
            BuildBlocks();
            BuildRoofs();
            BuildProps();
            BuildLights();
            BuildGarlands();
            BuildTown();
            BuildBackground();
            BuildProbes();
            BuildGameplay();
            var ui = BuildUI(out var input);
            BuildPlayers(ui, input);

            _meshes.Save();
            Lightmapping.lightingSettings = LightingSetup.GetOrCreate();
            EditorSceneManager.SaveScene(scene, CatsPaths.Level01Scene);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(CatsPaths.Level01Scene, true) };
            Debug.Log("[Cats] Level 01 built. Next: Cats ▸ 4. Bake Lighting (takes a few minutes), then press Play.");
        }

        // ------------------------------------------------------------------ environment
        static void BuildEnvironment(out Light moon)
        {
            var e = L.environment;
            RenderSettings.skybox = MaterialLibrary.Get("M_Sky");
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = e.ambientSky;
            RenderSettings.ambientEquatorColor = e.ambientEquator;
            RenderSettings.ambientGroundColor = e.ambientGround;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = e.fogColor;
            RenderSettings.fogStartDistance = e.fogStart;
            RenderSettings.fogEndDistance = e.fogEnd;
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Skybox;
            RenderSettings.reflectionIntensity = 1f;

            var go = new GameObject("Moonlight");
            go.transform.SetParent(_lights, false);
            moon = go.AddComponent<Light>();
            moon.type = LightType.Directional;
            moon.color = L.moon.color;
            moon.intensity = L.moon.intensity;
            moon.lightmapBakeType = LightmapBakeType.Mixed;
            moon.shadows = LightShadows.Soft;
            moon.shadowStrength = 0.75f;
            moon.shadowAngle = 1.2f;
            moon.transform.rotation = Quaternion.LookRotation(-L.MoonDirection);
            RenderSettings.sun = moon;

            var volGo = new GameObject("PostProcess");
            var vol = volGo.AddComponent<Volume>();
            vol.isGlobal = true;
            vol.sharedProfile = PostProfile();
        }

        static VolumeProfile PostProfile()
        {
            string path = CatsPaths.Settings + "/PP_Level01.asset";
            EditorUtil.EnsureFolder(CatsPaths.Settings);
            AssetDatabase.DeleteAsset(path);
            var p = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(p, path);
            T Add<T>() where T : VolumeComponent
            {
                var c = p.Add<T>(true);
                c.name = typeof(T).Name;
                AssetDatabase.AddObjectToAsset(c, p);
                return c;
            }
            var tone = Add<Tonemapping>();
            tone.mode.Override(TonemappingMode.ACES);
            var bloom = Add<Bloom>();
            bloom.threshold.Override(1.0f);
            bloom.intensity.Override(0.65f);
            bloom.scatter.Override(0.7f);
            bloom.tint.Override(new Color(1f, 0.9f, 0.8f));
            var split = Add<SplitToning>();
            split.shadows.Override(new Color(0.17f, 0.29f, 0.5f));
            split.highlights.Override(new Color(1f, 0.69f, 0.38f));
            split.balance.Override(-20f);
            var color = Add<ColorAdjustments>();
            color.postExposure.Override(0.25f);
            color.contrast.Override(12f);
            color.saturation.Override(8f);
            var vig = Add<Vignette>();
            vig.intensity.Override(0.25f);
            vig.smoothness.Override(0.4f);
            EditorUtility.SetDirty(p);
            AssetDatabase.SaveAssets();
            return p;
        }

        // ------------------------------------------------------------------ geometry
        static GameObject MeshObject(string name, Transform parent, Mesh mesh, Material mat, bool isStatic, bool shadows = true)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = mat;
            r.shadowCastingMode = shadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
            if (isStatic) GameObjectUtility.SetStaticEditorFlags(go, EditorUtil.LevelStatic | StaticEditorFlags.OccluderStatic);
            return go;
        }

        static void BuildBlocks()
        {
            foreach (var b in L.blocks)
            {
                var rot = Quaternion.Euler(b.rot);
                GameObject go;
                if (b.visible)
                {
                    Mf.Box(Vector3.zero, b.size, Matrix4x4.TRS(b.pos, rot, Vector3.one));
                    var mesh = _meshes.Add(Mf.ToMesh(b.name, b.isStatic));
                    go = MeshObject(b.name, _geo, mesh, MaterialLibrary.Get(b.mat), b.isStatic);
                }
                else
                {
                    go = new GameObject(b.name);
                    go.transform.SetParent(_geo, false);
                    go.layer = _catOnlyLayer;
                }
                go.transform.SetPositionAndRotation(b.pos, rot);
                if (b.collide)
                {
                    var col = go.AddComponent<BoxCollider>();
                    col.size = b.size;
                }
                if (!string.IsNullOrEmpty(b.surface))
                {
                    var tag = go.AddComponent<SurfaceTag>();
                    tag.kind = b.surface == "Slide" ? SurfaceKind.Slide : b.surface == "Ledge" ? SurfaceKind.Ledge : SurfaceKind.Normal;
                    if (tag.kind == SurfaceKind.Slide)
                        AddHint(b.pos + Vector3.up * 0.6f, b.size + new Vector3(0.6f, 1.2f, 0.6f), "Маркиза скользкая! Прыгай с неё на балкон ниже — там светится лапка.");
                }
            }
        }

        static void BuildRoofs()
        {
            foreach (var r in L.roofs)
            {
                Mf.GableRoof(Vector3.zero, r.size);
                var mesh = _meshes.Add(Mf.ToMesh("Roof", true));
                var go = MeshObject("Roof", _geo, mesh, MaterialLibrary.Get(r.mat), true);
                go.transform.SetPositionAndRotation(r.pos, Quaternion.Euler(0f, r.rotY, 0f));
                go.AddComponent<MeshCollider>().sharedMesh = mesh;
            }
        }

        // ------------------------------------------------------------------ props
        static void BuildProps()
        {
            var missing = new HashSet<string>();
            foreach (var p in L.props)
            {
                var go = PlaceProp(p.model, _props, p.pos, p.rotY, p.scale);
                if (go == null) { missing.Add(p.model); continue; }
                PrefabFactory.SwapMaterials(go, p.matSwap);
                if (p.collider == "box")
                {
                    var b = EditorUtil.LocalBounds(go.transform);
                    var col = go.AddComponent<BoxCollider>();
                    col.center = b.center;
                    col.size = b.size;
                }
                if (!p.isStatic && p.model.StartsWith("Pot_"))
                {
                    var rb = go.AddComponent<Rigidbody>();
                    rb.mass = 2f;
                }
                if (p.isStatic) MakeStatic(go, p.model);
                if (p.model == "Ship") go.AddComponent<ShipMover>();
                if (p.light != null && p.light.intensity > 0f)
                {
                    var anchor = EditorUtil.FindDeep(go.transform, "LightPoint") ?? go.transform;
                    var l = AddPointLight("Light", anchor, Vector3.zero, p.light.color, p.light.intensity, p.light.range, p.light.mode, p.light.shadows);
                    if (p.light.mode != "baked") l.gameObject.AddComponent<LightFlicker>();
                }
            }
            foreach (var m in missing) Debug.LogWarning($"[Cats] Prefab for model '{m}' missing");
        }

        static GameObject PlaceProp(string model, Transform parent, Vector3 pos, float rotY, Vector3 scale)
        {
            var prefab = PrefabFactory.Load(model);
            if (prefab == null) return null;
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
            go.transform.SetPositionAndRotation(pos, Quaternion.Euler(0f, rotY, 0f));
            go.transform.localScale = scale == Vector3.zero ? Vector3.one : scale;
            return go;
        }

        static void MakeStatic(GameObject go, string model)
        {
            EditorUtil.SetStaticRecursive(go, EditorUtil.LevelStatic);
            if (!PrefabFactory.SmallProps.Contains(model)) return;
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>()) r.receiveGI = ReceiveGI.LightProbes;
        }

        static Light AddPointLight(string name, Transform parent, Vector3 localPos, Color color, float intensity, float range, string mode, bool shadows)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var l = go.AddComponent<Light>();
            l.type = LightType.Point;
            l.color = color;
            l.intensity = intensity;
            l.range = range;
            l.bounceIntensity = 1f;
            l.lightmapBakeType = mode == "mixed" ? LightmapBakeType.Mixed : mode == "realtime" ? LightmapBakeType.Realtime : LightmapBakeType.Baked;
            l.shadows = l.lightmapBakeType == LightmapBakeType.Baked || shadows ? LightShadows.Soft : LightShadows.None;
            l.shadowRadius = 0.06f;
            return l;
        }

        static void BuildLights()
        {
            foreach (var d in L.lights)
            {
                var l = AddPointLight(d.name, _lights, Vector3.zero, d.color, d.intensity, d.range, d.mode, d.shadows);
                l.transform.position = d.pos;
            }
        }

        // ------------------------------------------------------------------ garlands
        static Vector3 Sag(Vector3 a, Vector3 b, float sag, float t)
        {
            var p = Vector3.Lerp(a, b, t);
            p.y -= sag * 4f * t * (1f - t);
            return p;
        }

        static void BuildGarlands()
        {
            int i = 0;
            foreach (var g in L.garlands)
            {
                var root = new GameObject("Garland" + i++).transform;
                root.SetParent(_props, false);
                var pts = new List<Vector3>();
                for (int k = 0; k <= 24; k++) pts.Add(Sag(g.a, g.b, g.sag, k / 24f));
                Mf.Tube(pts, 0.006f);
                MeshObject("Wire", root, _meshes.Add(Mf.ToMesh("GarlandWire", false)), MaterialLibrary.Get("M_Wire"), false, false);
                float len = Vector3.Distance(g.a, g.b);
                int n = Mathf.Max(2, Mathf.RoundToInt(len / g.bulbSpacing));
                for (int k = 1; k < n; k++)
                {
                    var bulb = PlaceProp("Bulb", root, Sag(g.a, g.b, g.sag, (float)k / n), 0f, Vector3.one);
                    if (bulb != null) EditorUtil.SetStaticRecursive(bulb, StaticEditorFlags.BatchingStatic);
                }
                var warm = new Color(1f, 0.72f, 0.4f);
                AddPointLight("GlowA", root, Sag(g.a, g.b, g.sag, 0.3f), warm, 0.9f, 3.5f, "baked", false);
                AddPointLight("GlowB", root, Sag(g.a, g.b, g.sag, 0.7f), warm, 0.9f, 3.5f, "baked", false);
                if (g.gameplay)
                {
                    var rope = root.gameObject.AddComponent<RopePath>();
                    rope.a = g.a;
                    rope.b = g.b;
                    rope.sag = g.sag;
                }
            }
        }

        // ------------------------------------------------------------------ distant town (combined per material)
        static void BuildTown()
        {
            var byMat = new Dictionary<string, MeshFactory>();
            MeshFactory For(string mat)
            {
                if (!byMat.TryGetValue(mat, out var f)) byMat[mat] = f = new MeshFactory();
                return f;
            }
            foreach (var h in L.houses)
            {
                var center = h.pos + Vector3.up * (h.size.y * 0.5f);
                For(h.mat).Box(center, h.size, Matrix4x4.identity, h.uvOffset, true);
                if (h.gable) For(h.roofMat).GableRoof(h.pos + Vector3.up * h.size.y, new Vector3(h.size.x + 0.6f, 2f, h.size.z + 0.6f));
                else For("M_Stone").Box(h.pos + Vector3.up * (h.size.y + 0.15f), new Vector3(h.size.x + 0.3f, 0.3f, h.size.z + 0.3f), Matrix4x4.identity);
                if (h.foundation > 0f)
                    For("M_Stone").Box(h.pos - Vector3.up * (h.foundation * 0.5f), new Vector3(h.size.x + 4f, h.foundation, h.size.z + 4f),
                        Matrix4x4.identity, 0f, true);
            }
            var root = new GameObject("Town").transform;
            root.SetParent(_background, false);
            foreach (var kv in byMat)
            {
                var go = MeshObject("Town_" + kv.Key, root, _meshes.Add(kv.Value.ToMesh("Town_" + kv.Key, false)), MaterialLibrary.Get(kv.Key), false);
                go.GetComponent<MeshRenderer>().receiveGI = ReceiveGI.LightProbes;
                GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic);
            }
        }

        static void BuildBackground()
        {
            var eye = L.spawn.p1;
            var bg = L.background;
            Mf.Arc(new Vector3(eye.x, 0f, eye.z), bg.radius, bg.y, bg.height, bg.arcStart, bg.arcEnd, 64);
            MeshObject("FarMatte", _background, _meshes.Add(Mf.ToMesh("FarMatte", false)), MaterialLibrary.Get("M_FarMatte"), false, false);

            var s = L.sea;
            Mf.FlatQuad(Vector3.zero, new Vector2(s.size.x, s.size.z), Vector3.up, new Vector2(s.size.x, s.size.z));
            var sea = MeshObject("Sea", _background, _meshes.Add(Mf.ToMesh("Sea", false)), MaterialLibrary.Get("M_Sea"), false, false);
            sea.transform.position = new Vector3(s.center.x, s.y, s.center.z);
            sea.AddComponent<WaterScroller>();

            Mf.FlatQuad(Vector3.zero, Vector2.one, Vector3.back, Vector2.one);
            var moon = MeshObject("MoonDisc", _background, _meshes.Add(Mf.ToMesh("MoonDisc", false)), MaterialLibrary.Get("M_Moon"), false, false);
            moon.transform.localScale = Vector3.one * L.moon.quadSize;
            var mb = moon.AddComponent<MoonBillboard>();
            mb.direction = L.MoonDirection;
            mb.distance = L.moon.quadDistance;
            moon.transform.position = eye + L.MoonDirection * L.moon.quadDistance;
            moon.transform.rotation = Quaternion.LookRotation(L.MoonDirection);
        }

        // ------------------------------------------------------------------ probes
        static void BuildProbes()
        {
            int i = 0;
            foreach (var p in L.reflectionProbes)
            {
                var go = new GameObject("ReflectionProbe" + i++);
                go.transform.SetParent(_probes, false);
                go.transform.position = p.pos;
                var rp = go.AddComponent<ReflectionProbe>();
                rp.mode = ReflectionProbeMode.Baked;
                rp.size = p.size + Vector3.one * 0.5f;
                rp.boxProjection = true;
                rp.importance = p.importance;
                rp.resolution = p.importance > 0 ? 128 : 64;
                rp.hdr = true;
                rp.blendDistance = 0.6f;
                rp.farClipPlane = 3000f;
            }
            var lp = new GameObject("LightProbes").AddComponent<LightProbeGroup>();
            lp.transform.SetParent(_probes, false);
            lp.probePositions = L.lightProbes;
        }

        // ------------------------------------------------------------------ gameplay
        static GameObject Trigger(string name, Vector3 pos, Vector3 size)
        {
            var go = new GameObject(name);
            go.transform.SetParent(_gameplay, false);
            go.transform.position = pos;
            go.layer = _ignoreRaycastLayer;
            var c = go.AddComponent<BoxCollider>();
            c.isTrigger = true;
            c.size = size;
            return go;
        }

        static void AddHint(Vector3 pos, Vector3 size, string text)
        {
            var h = Trigger("Hint", pos, size).AddComponent<HintZone>();
            h.text = text;
        }

        static void BuildGameplay()
        {
            Mf.FlatQuad(Vector3.zero, new Vector2(0.34f, 0.34f), Vector3.up, Vector2.one);
            var pawMesh = _meshes.Add(Mf.ToMesh("PawMarker", false));
            int i = 0;
            foreach (var m in L.markers)
            {
                var go = MeshObject("PawMarker" + i++, _gameplay, pawMesh, MaterialLibrary.Get("M_PawMarker"), false, false);
                go.transform.position = m.pos + Vector3.up * 0.012f;
                go.AddComponent<JumpMarker>();
            }
            foreach (var c in L.checkpoints)
            {
                var cp = Trigger("Checkpoint_" + c.id, c.pos, c.size).AddComponent<Checkpoint>();
                cp.id = c.id;
                cp.spawnYaw = c.spawnRotY;
            }
            foreach (var k in L.killZones) Trigger("KillZone", k.pos, k.size).AddComponent<KillZone>();
            foreach (var z in L.cameraZones)
            {
                var cz = Trigger("CameraZone", z.pos, z.size).AddComponent<CameraZone>();
                cz.distance = z.distance;
                cz.height = z.height;
                cz.pitch = z.pitch;
                cz.side = z.side;
            }
            foreach (var z in L.ledgeZones) Trigger("LedgeZone", z.pos, z.size).AddComponent<LedgeZone>();
            Trigger("LevelExit", L.exit.pos, L.exit.size).AddComponent<LevelExit>();
            AddHint(L.spawn.p1 + new Vector3(0f, 0.5f, 3.2f), new Vector3(2.6f, 1.2f, 1.6f), "Видишь светящуюся лапку? Подойди и нажми прыжок.");

            // Baron, the neighbour cat
            var npc = PlaceProp(L.npc.model, _gameplay, L.npc.pos, L.npc.rotY, Vector3.one);
            if (npc != null)
            {
                var talk = new GameObject("Talk");
                talk.transform.SetParent(npc.transform, false);
                talk.layer = _ignoreRaycastLayer;
                var sc = talk.AddComponent<SphereCollider>();
                sc.isTrigger = true;
                sc.radius = L.npc.radius;
                var nc = talk.AddComponent<NpcCat>();
                nc.head = EditorUtil.FindDeep(npc.transform, "Head");
                var body = npc.AddComponent<BoxCollider>();
                body.center = new Vector3(0f, 0.25f, 0f);
                body.size = new Vector3(0.25f, 0.5f, 0.3f);
            }
        }

        // ------------------------------------------------------------------ UI
        static Font UIFont => Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        static Sprite Sprite(string name) => AssetDatabase.LoadAssetAtPath<Sprite>($"{CatsPaths.Textures}/{name}.png");

        static RectTransform Rect(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size)
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

        static RectTransform Stretch(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            return rt;
        }

        static Image Img(RectTransform rt, string sprite, Color color, bool raycast)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = sprite != null ? Sprite(sprite) : null;
            img.color = color;
            img.raycastTarget = raycast;
            return img;
        }

        static Text Label(RectTransform rt, int size, TextAnchor align, Color color)
        {
            var t = rt.gameObject.AddComponent<Text>();
            t.font = UIFont;
            t.fontSize = size;
            t.alignment = align;
            t.color = color;
            t.raycastTarget = false;
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            return t;
        }

        static GameUI BuildUI(out LocalCatInput input)
        {
            var es = new GameObject("EventSystem");
            es.AddComponent<EventSystem>();
#if ENABLE_INPUT_SYSTEM
            es.AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
#else
            es.AddComponent<StandaloneInputModule>();
#endif
            var canvasGo = new GameObject("UI", typeof(RectTransform));
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 1f;
            canvasGo.AddComponent<GraphicRaycaster>();
            var root = canvasGo.transform;
            var ui = canvasGo.AddComponent<GameUI>();

            var controls = Stretch("TouchControls", root);
            var look = Stretch("LookArea", controls);
            Img(look, null, new Color(0, 0, 0, 0), true);
            var lookArea = look.gameObject.AddComponent<LookArea>();

            var stick = Rect("Joystick", controls, new Vector2(0, 0), new Vector2(230, 230), new Vector2(260, 260));
            Img(stick, "UI_JoystickBase", new Color(1, 1, 1, 0.85f), true);
            var knob = Rect("Knob", stick, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(120, 120));
            Img(knob, "UI_JoystickKnob", new Color(1, 1, 1, 0.85f), false);
            var joystick = stick.gameObject.AddComponent<VirtualJoystick>();
            joystick.knob = knob;
            joystick.radius = 100f;

            var jump = Rect("JumpButton", controls, new Vector2(1, 0), new Vector2(-230, 230), new Vector2(230, 230));
            Img(jump, "UI_JumpButton", new Color(1, 1, 1, 0.9f), true);
            var jumpButton = jump.gameObject.AddComponent<JumpButton>();

            var hint = Rect("Hint", root, new Vector2(0.5f, 1f), new Vector2(0, -90), new Vector2(1500, 110));
            Img(hint, "UI_Panel", new Color(0.02f, 0.03f, 0.08f, 0.55f), false);
            ui.hintGroup = hint.gameObject.AddComponent<CanvasGroup>();
            ui.hintGroup.blocksRaycasts = false;
            var hintText = Stretch("Text", hint);
            hintText.offsetMin = new Vector2(30, 8);
            hintText.offsetMax = new Vector2(-30, -8);
            ui.hintText = Label(hintText, 38, TextAnchor.MiddleCenter, new Color(1f, 0.95f, 0.85f));

            var dlg = Rect("Dialogue", root, new Vector2(0.5f, 0f), new Vector2(0, 140), new Vector2(1150, 190));
            Img(dlg, "UI_Panel", new Color(0.02f, 0.03f, 0.08f, 0.7f), false);
            ui.dialogueGroup = dlg.gameObject.AddComponent<CanvasGroup>();
            ui.dialogueGroup.blocksRaycasts = false;
            var dn = Rect("Name", dlg, new Vector2(0f, 1f), new Vector2(180, -32), new Vector2(320, 50));
            ui.dialogueName = Label(dn, 34, TextAnchor.MiddleLeft, new Color(1f, 0.72f, 0.38f));
            var dt = Stretch("Line", dlg);
            dt.offsetMin = new Vector2(40, 16);
            dt.offsetMax = new Vector2(-40, -60);
            ui.dialogueText = Label(dt, 40, TextAnchor.UpperLeft, Color.white);

            var fin = Rect("Finish", root, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1100, 320));
            Img(fin, "UI_Panel", new Color(0.02f, 0.03f, 0.08f, 0.75f), false);
            ui.finishGroup = fin.gameObject.AddComponent<CanvasGroup>();
            ui.finishGroup.blocksRaycasts = false;
            ui.finishText = Label(Stretch("Text", fin), 58, TextAnchor.MiddleCenter, new Color(1f, 0.9f, 0.7f));

            var fade = Stretch("Fade", root);
            Img(fade, null, Color.black, false);
            ui.fade = fade.gameObject.AddComponent<CanvasGroup>();
            ui.fade.blocksRaycasts = false;
            ui.fade.interactable = false;
            ui.touchControls = controls.gameObject;

            var inputGo = new GameObject("LocalInput");
            input = inputGo.AddComponent<LocalCatInput>();
            input.joystick = joystick;
            input.jumpButton = jumpButton;
            input.lookArea = lookArea;
            return ui;
        }

        // ------------------------------------------------------------------ players + camera
        static void BuildPlayers(GameUI ui, LocalCatInput input)
        {
            var player = new GameObject("Player1");
            player.transform.SetPositionAndRotation(L.spawn.p1, Quaternion.Euler(0f, L.spawn.rotY, 0f));
            var cc = player.AddComponent<CharacterController>();
            cc.radius = 0.13f;
            cc.height = 0.34f;
            cc.center = new Vector3(0f, 0.185f, 0f);
            cc.stepOffset = 0.2f;
            cc.slopeLimit = 50f;
            cc.skinWidth = 0.015f;
            cc.minMoveDistance = 0f;
            var model = PlaceProp("Cat_Hero", player.transform, L.spawn.p1, L.spawn.rotY, Vector3.one);
            if (model != null) model.name = "Model";
            EditorUtil.SetLayerRecursive(player, _playerLayer);

            var cat = player.AddComponent<CatController>();
            cat.environmentMask = ~((1 << _playerLayer) | (1 << _ignoreRaycastLayer));
            var anim = player.AddComponent<CatAnimator>();
            anim.controller = cat;
            anim.model = model != null ? model.transform : player.transform;

            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 50f;
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 4000f;
            cam.allowHDR = true;
            cam.clearFlags = CameraClearFlags.Skybox;
            camGo.AddComponent<AudioListener>();
            var data = cam.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = true;
            data.antialiasing = AntialiasingMode.FastApproximateAntialiasing;
            var rig = camGo.AddComponent<CatCameraRig>();
            rig.target = player.transform;
            rig.collisionMask = ~((1 << _playerLayer) | (1 << _ignoreRaycastLayer) | (1 << _catOnlyLayer));
            camGo.transform.position = L.startCamera.pos;
            camGo.transform.rotation = Quaternion.LookRotation(L.startCamera.lookAt - L.startCamera.pos);

            input.cameraRig = rig;
            cat.input = input;
            cat.cameraRig = rig;

            var p2 = new GameObject("SpawnPlayer2 (co-op)");
            p2.transform.SetPositionAndRotation(L.spawn.p2, Quaternion.Euler(0f, L.spawn.rotY, 0f));

            var gm = new GameObject("GameManager").AddComponent<GameManager>();
            gm.ui = ui;
            gm.player2Spawn = p2.transform;
            gm.players.Add(new GameManager.PlayerSlot { cat = cat, rig = rig });
        }
    }
}
