using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Cats.EditorTools
{
    /// <summary>
    /// Second pass of the level build: everything that makes the place feel alive —
    /// lantern halos and light shafts, window light spilling on the walls, wall grime, clouds,
    /// moon halo and moon path, moths, fireflies, drips, dust, pigeons, wind, sounds.
    /// </summary>
    public static class Level01Atmosphere
    {
        static readonly Color Warm = new Color(1f, 0.66f, 0.36f);

        public static void Build(LevelData L, Transform props, Transform background, MeshFactory.Bundle meshes, Transform player, Camera cam)
        {
            var root = new GameObject("Atmosphere").transform;
            var mf = new MeshFactory();
            BuildDecals(L, root, mf, meshes);
            BuildLightShaftsAndGlows(props, root, mf, meshes);
            BuildSky(L, background, mf, meshes);
            BuildParticles(L, props, root, cam);
            BuildLife(L, root, player, meshes);
            ApplyWind(props);
            BuildAudio(L, props, root, player);
        }

        static AudioClip Clip(string name) => AssetDatabase.LoadAssetAtPath<AudioClip>($"{CatsPaths.Root}/Audio/{name}.wav");

        static GameObject Mesh(string name, Transform parent, Mesh mesh, string mat)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = MaterialLibrary.Get(mat);
            r.shadowCastingMode = ShadowCastingMode.Off;
            r.receiveShadows = false;
            r.lightProbeUsage = LightProbeUsage.Off;
            r.reflectionProbeUsage = ReflectionProbeUsage.Off;
            return go;
        }

        // ------------------------------------------------------------------ grime / streak decals
        static void BuildDecals(LevelData L, Transform root, MeshFactory mf, MeshFactory.Bundle meshes)
        {
            if (L.decals == null) return;
            var byMat = new Dictionary<string, MeshFactory>();
            foreach (var d in L.decals)
            {
                if (!byMat.TryGetValue(d.mat, out var f)) byMat[d.mat] = f = new MeshFactory();
                var n = d.a.x < 2.6f ? Vector3.right : Vector3.left;
                f.Quad(d.a, d.b, d.c, d.d, n, Vector2.zero, new Vector2(d.uv.x, 0f), new Vector2(d.uv.x, d.uv.y), new Vector2(0f, d.uv.y));
            }
            foreach (var kv in byMat)
            {
                var go = Mesh("Decals_" + kv.Key, root, meshes.Add(kv.Value.ToMesh("Decals_" + kv.Key, false)), kv.Key);
                GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic);
            }
        }

        // ------------------------------------------------------------------ halos, light shafts, window spill
        static void BuildLightShaftsAndGlows(Transform props, Transform root, MeshFactory mf, MeshFactory.Bundle meshes)
        {
            mf.Cone(3.0f, 1.25f);
            var streetCone = meshes.Add(mf.ToMesh("Cone_StreetLamp", false));
            mf.Cone(1.9f, 0.85f, 0.04f);
            var wallCone = meshes.Add(mf.ToMesh("Cone_Lantern", false));

            var pos = new List<Vector3>();
            var size = new List<float>();
            var col = new List<Color>();
            void Glow(Vector3 p, float s, float a) { pos.Add(p); size.Add(s); col.Add(new Color(1f, 1f, 1f, a)); }

            var spill = new GameObject("WindowSpill").transform;
            spill.SetParent(root, false);
            foreach (Transform t in props.GetComponentsInChildren<Transform>())
            {
                string n = t.name;
                if (t.parent == null) continue;
                if (n == "Lantern_Wall" || n == "StreetLamp")
                {
                    var lp = EditorUtil.FindDeep(t, "LightPoint");
                    var p = lp != null ? lp.position : t.position;
                    bool street = n == "StreetLamp";
                    Glow(p, street ? 1.5f : 1.1f, 0.65f);
                    var cone = Mesh("LightShaft", root, street ? streetCone : wallCone, "M_LightCone");
                    cone.transform.position = p + Vector3.down * 0.12f;
                    GameObjectUtility.SetStaticEditorFlags(cone, StaticEditorFlags.BatchingStatic);
                }
                else if (n == "Bulb")
                {
                    Glow(t.position + Vector3.down * 0.045f, 0.32f, 0.55f);
                }
                else if (n.StartsWith("Window_Lit") || n == "Door_Balcony")
                {
                    bool door = n == "Door_Balcony";
                    var center = t.TransformPoint(new Vector3(0f, door ? 1.2f : 0.7f, 0.04f));
                    Glow(center, door ? 2.6f : 1.7f, door ? 0.2f : 0.16f);
                    // warm light falling from the window onto the wall, sill and street below
                    var go = new GameObject("Spill_" + n);
                    go.transform.SetParent(spill, false);
                    go.transform.position = t.TransformPoint(new Vector3(0f, door ? 1.4f : 0.9f, 0.55f));
                    var l = go.AddComponent<Light>();
                    l.type = LightType.Point;
                    l.color = new Color(1f, 0.7f, 0.42f);
                    l.intensity = (door ? 1.2f : 0.7f) * Level01Builder.LightBoost;
                    l.range = door ? 4f : 2.8f;
                    l.lightmapBakeType = LightmapBakeType.Baked;
                    l.shadows = LightShadows.Soft;
                    l.shadowRadius = 0.1f;
                }
                else if (n == "BellTower" || n == "Lighthouse")
                {
                    var lp = EditorUtil.FindDeep(t, "LightPoint");
                    if (lp != null) Glow(lp.position, n == "BellTower" ? 9f : 12f, 0.5f);
                }
            }

            var glowGo = new GameObject("LanternGlow");
            glowGo.transform.SetParent(root, false);
            var ps = glowGo.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.loop = true;
            main.playOnAwake = true;
            main.startSpeed = 0f;
            main.startLifetime = 1e6f;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = Mathf.Max(1, pos.Count);
            main.cullingMode = ParticleSystemCullingMode.AlwaysSimulate;
            var em = ps.emission;
            em.enabled = false;
            var sh = ps.shape;
            sh.enabled = false;
            var pr = glowGo.GetComponent<ParticleSystemRenderer>();
            pr.sharedMaterial = MaterialLibrary.Get("M_Glow");
            pr.renderMode = ParticleSystemRenderMode.Billboard;
            pr.sortMode = ParticleSystemSortMode.Distance;
            pr.maxParticleSize = 4f;
            pr.shadowCastingMode = ShadowCastingMode.Off;
            pr.receiveShadows = false;
            var field = glowGo.AddComponent<Cats.GlowField>();
            field.positions = pos.ToArray();
            field.sizes = size.ToArray();
            field.colors = col.ToArray();
        }

        // ------------------------------------------------------------------ sky: clouds, moon halo, moon path
        static void BuildSky(LevelData L, Transform bg, MeshFactory mf, MeshFactory.Bundle meshes)
        {
            var eye = L.spawn.p1;
            mf.Arc(new Vector3(eye.x, 0f, eye.z), 1350f, 40f, 420f, -180f, 180f, 72);
            var clouds = Mesh("Clouds", bg, meshes.Add(mf.ToMesh("Clouds", false)), "M_Clouds");
            var scroll = clouds.AddComponent<Cats.WaterScroller>();
            scroll.speed = new Vector2(0.0008f, 0f);

            var moon = GameObject.Find("MoonDisc");
            if (moon != null)
            {
                mf.FlatQuad(Vector3.zero, Vector2.one * 4f, Vector3.back, Vector2.one);
                var halo = Mesh("MoonHalo", moon.transform, meshes.Add(mf.ToMesh("MoonHalo", false)), "M_MoonHalo");
                halo.transform.localPosition = new Vector3(0f, 0f, 0.5f);
            }

            // light trails of the shore lights, the lighthouse, the quay lamps and the cruise ship on the water
            var glintPos = new List<Vector3>();
            var glintStrength = new List<float>();
            var rnd = new System.Random(7);
            if (L.houses != null)
                for (int i = 0; i < L.houses.Length; i += 2)
                {
                    var h = L.houses[i];
                    if (h.pos.z < 95f || h.pos.y > -2f) continue;
                    glintPos.Add(h.pos);
                    glintStrength.Add(0.35f + 0.65f * (float)rnd.NextDouble());
                }
            Transform ship = null;
            foreach (Transform t in GameObject.Find("Props").GetComponentsInChildren<Transform>())
            {
                if (t.name == "Lighthouse") { glintPos.Add(t.position); glintStrength.Add(1.6f); }
                else if (t.name == "StreetLamp" && t.position.z > 85f) { glintPos.Add(t.position); glintStrength.Add(1.2f); }
                else if (t.name == "Ship") ship = t;
            }
            var glints = new GameObject("SeaGlints");
            glints.transform.SetParent(bg, false);
            glints.AddComponent<MeshFilter>();
            var gr = glints.AddComponent<MeshRenderer>();
            gr.sharedMaterial = MaterialLibrary.Get("M_SeaGlint");
            gr.shadowCastingMode = ShadowCastingMode.Off;
            gr.receiveShadows = false;
            gr.lightProbeUsage = LightProbeUsage.Off;
            gr.reflectionProbeUsage = ReflectionProbeUsage.Off;
            var sg = glints.AddComponent<Cats.SeaGlints>();
            sg.lights = glintPos.ToArray();
            sg.strength = glintStrength.ToArray();
            sg.movingLights = ship != null ? new[] { ship } : new Transform[0];
            sg.seaLevel = L.sea.y + 0.04f;

            mf.FlatQuad(Vector3.zero, Vector2.one, Vector3.up, Vector2.one);
            var path = Mesh("MoonPath", bg, meshes.Add(mf.ToMesh("MoonPath", false)), "M_MoonPath");
            var mp = path.AddComponent<Cats.MoonPath>();
            mp.moonDirection = L.MoonDirection;
            mp.seaLevel = L.sea.y + 0.05f;
        }

        // ------------------------------------------------------------------ particles
        static ParticleSystem Particles(string name, Transform parent, Vector3 pos, string mat, int max)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var ps = go.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.maxParticles = max;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.startSpeed = 0f;
            main.playOnAwake = true;
            main.loop = true;
            main.prewarm = true;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = MaterialLibrary.Get(mat);
            r.shadowCastingMode = ShadowCastingMode.Off;
            r.receiveShadows = false;
            r.maxParticleSize = 1f;
            return ps;
        }

        static Gradient Fade(float peak)
        {
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(peak, 0.2f), new GradientAlphaKey(peak, 0.7f), new GradientAlphaKey(0f, 1f) });
            return g;
        }

        static void BuildParticles(LevelData L, Transform props, Transform root, Camera cam)
        {
            var parent = new GameObject("Particles").transform;
            parent.SetParent(root, false);

            // moths around the lanterns along the route
            int moths = 0;
            foreach (Transform t in props.GetComponentsInChildren<Transform>())
            {
                if (t.name != "Lantern_Wall" || moths >= 14) continue;
                var lp = EditorUtil.FindDeep(t, "LightPoint");
                if (lp == null) continue;
                moths++;
                var ps = Particles("Moths", parent, lp.position, "M_Moth", 5);
                var main = ps.main;
                main.startLifetime = new ParticleSystem.MinMaxCurve(3f, 6f);
                main.startSize = new ParticleSystem.MinMaxCurve(0.025f, 0.04f);
                var em = ps.emission;
                em.rateOverTime = 1f;
                var sh = ps.shape;
                sh.shapeType = ParticleSystemShapeType.Sphere;
                sh.radius = 0.25f;
                var noise = ps.noise;
                noise.enabled = true;
                noise.strength = 0.9f;
                noise.frequency = 1.2f;
                noise.scrollSpeed = 0.6f;
                var c = ps.colorOverLifetime;
                c.enabled = true;
                c.color = Fade(1f);
            }

            if (L.fireflies != null)
                foreach (var z in L.fireflies)
                {
                    var ps = Particles("Fireflies", parent, z.pos, "M_Firefly", 14);
                    var main = ps.main;
                    main.startLifetime = new ParticleSystem.MinMaxCurve(4f, 8f);
                    main.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.09f);
                    var em = ps.emission;
                    em.rateOverTime = 2f;
                    var sh = ps.shape;
                    sh.shapeType = ParticleSystemShapeType.Box;
                    sh.scale = z.size;
                    var noise = ps.noise;
                    noise.enabled = true;
                    noise.strength = 0.35f;
                    noise.frequency = 0.4f;
                    var c = ps.colorOverLifetime;
                    c.enabled = true;
                    var g = new Gradient();
                    g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                        new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.15f), new GradientAlphaKey(0.1f, 0.35f),
                                new GradientAlphaKey(1f, 0.55f), new GradientAlphaKey(0.2f, 0.8f), new GradientAlphaKey(0f, 1f) });
                    c.color = g;
                }

            if (L.drips != null)
                foreach (var z in L.drips)
                {
                    var ps = Particles("Drips", parent, z.pos, "M_Drop", 12);
                    var main = ps.main;
                    main.startLifetime = 1.4f;
                    main.startSize = 0.03f;
                    main.gravityModifier = 1f;
                    main.prewarm = false;
                    var em = ps.emission;
                    em.rateOverTime = 1.2f;
                    var sh = ps.shape;
                    sh.shapeType = ParticleSystemShapeType.Box;
                    sh.scale = z.size;
                    var r = ps.GetComponent<ParticleSystemRenderer>();
                    r.renderMode = ParticleSystemRenderMode.Stretch;
                    r.velocityScale = 0.04f;
                    r.lengthScale = 1.5f;
                    var col = ps.collision;
                    col.enabled = true;
                    col.type = ParticleSystemCollisionType.World;
                    col.quality = ParticleSystemCollisionQuality.Low;
                    col.lifetimeLoss = 1f;
                    col.collidesWith = ~0;
                }

            if (L.ripples != null)
                foreach (var z in L.ripples)
                {
                    var ps = Particles("Ripples", parent, z.pos, "M_Ripple", 10);
                    var main = ps.main;
                    main.startLifetime = 0.9f;
                    main.startSize = 0.05f;
                    var em = ps.emission;
                    em.rateOverTime = 0.9f;
                    var sh = ps.shape;
                    sh.shapeType = ParticleSystemShapeType.Box;
                    sh.scale = z.size;
                    var sz = ps.sizeOverLifetime;
                    sz.enabled = true;
                    sz.size = new ParticleSystem.MinMaxCurve(5f, AnimationCurve.Linear(0f, 0.2f, 1f, 1f));
                    var c = ps.colorOverLifetime;
                    c.enabled = true;
                    var g = new Gradient();
                    g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                        new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(0f, 1f) });
                    c.color = g;
                    ps.GetComponent<ParticleSystemRenderer>().renderMode = ParticleSystemRenderMode.HorizontalBillboard;
                }

            // floating dust / pollen in front of the camera, catches the lantern light
            if (cam != null)
            {
                var ps = Particles("Dust", cam.transform, cam.transform.position, "M_Dust", 40);
                ps.gameObject.layer = ProjectSetup.Layer(ProjectSetup.FxLayer);
                ps.transform.localPosition = new Vector3(0f, 0f, 3.5f);
                var main = ps.main;
                main.simulationSpace = ParticleSystemSimulationSpace.Local;
                main.startLifetime = new ParticleSystem.MinMaxCurve(5f, 9f);
                main.startSize = new ParticleSystem.MinMaxCurve(0.008f, 0.02f);
                var em = ps.emission;
                em.rateOverTime = 5f;
                var sh = ps.shape;
                sh.shapeType = ParticleSystemShapeType.Box;
                sh.scale = new Vector3(5f, 3f, 5f);
                var noise = ps.noise;
                noise.enabled = true;
                noise.strength = 0.08f;
                noise.frequency = 0.3f;
                var c = ps.colorOverLifetime;
                c.enabled = true;
                c.color = Fade(1f);
            }

            if (L.tvLights != null)
                foreach (var tv in L.tvLights)
                {
                    var go = new GameObject("TV_Light");
                    go.transform.SetParent(parent, false);
                    go.transform.position = tv.pos;
                    var l = go.AddComponent<Light>();
                    l.type = LightType.Point;
                    l.range = 5f;
                    l.intensity = 1.2f;
                    l.lightmapBakeType = LightmapBakeType.Realtime;
                    l.shadows = LightShadows.None;
                    go.AddComponent<Cats.WindowFlicker>();
                }
        }

        // ------------------------------------------------------------------ pigeons, breakable pots, footprints
        static void BuildLife(LevelData L, Transform root, Transform player, MeshFactory.Bundle meshes)
        {
            var life = new GameObject("Life").transform;
            life.SetParent(root, false);
            var prefab = PrefabFactory.Load("Pigeon");
            if (prefab != null && L.pigeons != null)
                foreach (var p in L.pigeons)
                {
                    var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, life);
                    go.transform.SetPositionAndRotation(p.pos, Quaternion.Euler(0f, p.rotY, 0f));
                    var pg = go.AddComponent<Cats.Pigeon>();
                    pg.flap = Clip("sfx_pigeon_flap");
                    pg.coo = Clip("sfx_pigeon_coo");
                    pg.cat = player;
                }

            foreach (var rb in EditorUtil.FindAll<Rigidbody>())
            {
                if (!rb.name.StartsWith("Pot_")) continue;
                var pb = rb.gameObject.AddComponent<Cats.PotBreaker>();
                pb.breakClip = Clip("sfx_pot_break");
                pb.shardMaterial = MaterialLibrary.Get("M_Terracotta");
            }

            if (player != null)
            {
                var mf = new MeshFactory();
                mf.FlatQuad(Vector3.zero, Vector2.one, Vector3.back, Vector2.one);
                var fp = player.gameObject.AddComponent<Cats.CatFootprints>();
                fp.printMaterial = MaterialLibrary.Get("M_PawPrint");
                fp.quad = meshes.Add(mf.ToMesh("PawPrintQuad", false));
            }
        }

        // ------------------------------------------------------------------ wind
        static void ApplyWind(Transform props)
        {
            foreach (Transform t in props.GetComponentsInChildren<Transform>())
            {
                float amp, speed;
                Vector3 axis = Vector3.forward;
                switch (t.name)
                {
                    case "Laundry_Line": amp = 7f; speed = 0.7f; axis = Vector3.right; break;
                    case "Bulb": amp = 6f; speed = 0.9f; break;
                    case "Palm": amp = 1.2f; speed = 0.35f; break;
                    case "Cypress": amp = 0.8f; speed = 0.3f; break;
                    case "Bougainvillea": amp = 2.5f; speed = 0.5f; axis = Vector3.right; break;
                    default: continue;
                }
                EditorUtil.SetStaticRecursive(t.gameObject, 0);
                foreach (var r in t.GetComponentsInChildren<MeshRenderer>()) r.receiveGI = ReceiveGI.LightProbes;
                var w = t.gameObject.AddComponent<Cats.WindSway>();
                w.amplitude = amp;
                w.speed = speed;
                w.axis = axis;
            }
        }

        // ------------------------------------------------------------------ sound
        static void BuildAudio(LevelData L, Transform props, Transform root, Transform player)
        {
            var sounds = new GameObject("Sounds").transform;
            sounds.SetParent(root, false);
            if (L.sounds != null)
                foreach (var s in L.sounds)
                {
                    var go = new GameObject("Sound_" + s.clip);
                    go.transform.SetParent(sounds, false);
                    go.transform.position = s.pos;
                    var a = go.AddComponent<AudioSource>();
                    a.clip = Clip(s.clip);
                    a.loop = true;
                    a.playOnAwake = true;
                    a.volume = s.volume;
                    a.spatialBlend = 1f;
                    a.rolloffMode = AudioRolloffMode.Logarithmic;
                    a.minDistance = s.minDistance;
                    a.maxDistance = s.maxDistance;
                    a.dopplerLevel = 0f;
                    go.AddComponent<Cats.AudioVolume>().category = Cats.AudioVolume.Category.Music;
                }

            Transform bell = null;
            foreach (Transform t in props.GetComponentsInChildren<Transform>()) if (t.name == "BellTower") bell = t;
            var amb = new GameObject("AmbientAudio").AddComponent<Cats.AmbientAudio>();
            amb.transform.SetParent(sounds, false);
            amb.sea = Clip("amb_sea");
            amb.crickets = Clip("amb_crickets");
            amb.wind = Clip("amb_wind");
            amb.bell = Clip("sfx_bell_far");
            amb.listener = player;
            amb.bellTower = bell;

            if (player != null)
            {
                var ca = player.gameObject.AddComponent<Cats.CatAudio>();
                ca.steps = new[] { Clip("sfx_step_1"), Clip("sfx_step_2"), Clip("sfx_step_3"), Clip("sfx_step_4") };
                ca.stepMetal = Clip("sfx_step_metal");
                ca.jump = Clip("sfx_jump");
                ca.land = Clip("sfx_land");
                ca.meows = new[] { Clip("sfx_meow_1"), Clip("sfx_meow_2"), Clip("sfx_meow_3") };
                ca.purrLoop = Clip("sfx_purr_loop");
                ca.ropeCreak = Clip("sfx_rope_creak");
            }
            foreach (var npc in EditorUtil.FindAll<Cats.NpcCat>()) npc.meow = Clip("sfx_meow_baron");
        }
    }
}
