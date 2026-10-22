using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Rendering.Universal.ShaderGUI;
using UnityEngine;

namespace Cats.EditorTools
{
    /// <summary>Creates / updates URP materials from Data/materials.json.</summary>
    public static class MaterialLibrary
    {
        static Dictionary<string, Material> _cache;

        public static Dictionary<string, Material> All
        {
            get
            {
                if (_cache == null) Load();
                return _cache;
            }
        }

        public static Material Get(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            All.TryGetValue(name, out var m);
            if (m == null) Debug.LogWarning($"[Cats] Material '{name}' is missing — run Cats ▸ Build Materials.");
            return m;
        }

        static void Load()
        {
            _cache = new Dictionary<string, Material>();
            foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { CatsPaths.Materials }))
            {
                var m = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                if (m != null) _cache[m.name] = m;
            }
        }

        public static void BuildAll()
        {
            var json = AssetDatabase.LoadAssetAtPath<TextAsset>(CatsPaths.Data + "/materials.json");
            if (json == null)
            {
                Debug.LogError("[Cats] Data/materials.json not found.");
                return;
            }
            var lib = JsonUtility.FromJson<MaterialLibraryData>(json.text);
            EditorUtil.EnsureFolder(CatsPaths.Materials);
            foreach (var def in lib.materials) Build(def);
            AssetDatabase.SaveAssets();
            _cache = null;
            Debug.Log($"[Cats] {lib.materials.Length} materials ready in {CatsPaths.Materials}");
        }

        static Texture2D Tex(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            var t = AssetDatabase.LoadAssetAtPath<Texture2D>($"{CatsPaths.Textures}/{name}.png");
            if (t == null) Debug.LogWarning($"[Cats] Texture {name} not found");
            return t;
        }

        static void Build(MaterialDef d)
        {
            string path = $"{CatsPaths.Materials}/{d.name}.mat";
            string shaderName = d.shader switch
            {
                "skybox" => "Skybox/Panoramic",
                "puddle" => "Cats/PuddleReflection",
                "unlitCutout" => "Universal Render Pipeline/Unlit",
                "unlitTransparent" => "Universal Render Pipeline/Unlit",
                "unlitAdditive" => "Universal Render Pipeline/Unlit",
                "particlesAdditive" => "Universal Render Pipeline/Particles/Unlit",
                _ => "Universal Render Pipeline/Lit",
            };
            var shader = Shader.Find(shaderName);
            if (shader == null)
            {
                Debug.LogError($"[Cats] Shader {shaderName} not found. Is URP installed and set up (Cats ▸ 1)?");
                return;
            }
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            bool created = mat == null;
            if (created) mat = new Material(shader) { name = d.name };
            else mat.shader = shader;

            if (d.shader == "puddle")
            {
                mat.SetTexture("_MaskTex", Tex(d.mask));
                mat.SetTextureScale("_MaskTex", d.tiling);
                mat.SetTexture("_NormalTex", Tex(d.normal));
                mat.SetTextureScale("_NormalTex", d.tiling);
                mat.SetColor("_Tint", d.color);
                mat.SetFloat("_Strength", d.smoothness);
                mat.renderQueue = 2990;
            }
            else if (d.shader == "skybox")
            {
                mat.SetTexture("_MainTex", Tex(d.albedo));
                mat.SetFloat("_Mapping", 1f);
                mat.SetFloat("_ImageType", 0f);
                mat.SetFloat("_Exposure", 1f);
                mat.SetFloat("_Rotation", 0f);
                mat.EnableKeyword("_MAPPING_LATITUDE_LONGITUDE_LAYOUT");
                mat.DisableKeyword("_MAPPING_6_FRAMES_LAYOUT");
            }
            else
            {
                var albedo = Tex(d.albedo);
                mat.SetTexture("_BaseMap", albedo);
                mat.SetColor("_BaseColor", d.color);
                mat.SetTextureScale("_BaseMap", d.tiling);
                bool lit = shaderName.EndsWith("/Lit");
                if (lit)
                {
                    mat.SetFloat("_WorkflowMode", 1f);
                    var normal = Tex(d.normal);
                    mat.SetTexture("_BumpMap", normal);
                    mat.SetFloat("_BumpScale", d.normalScale);
                    var mask = Tex(d.mask);
                    mat.SetTexture("_MetallicGlossMap", mask);
                    mat.SetTexture("_OcclusionMap", mask);
                    mat.SetFloat("_OcclusionStrength", mask != null ? 1f : 0f);
                    mat.SetFloat("_SmoothnessTextureChannel", 0f);
                    mat.SetFloat("_Smoothness", mask != null ? 1f : d.smoothness);
                    mat.SetFloat("_Metallic", d.metallic);
                    bool emissive = d.emissionColor.maxColorComponent > 0.001f;
                    mat.SetColor("_EmissionColor", emissive ? d.emissionColor : Color.black);
                    mat.SetTexture("_EmissionMap", emissive ? Tex(d.emission) : null);
                    mat.globalIlluminationFlags = emissive ? MaterialGlobalIlluminationFlags.BakedEmissive
                                                           : MaterialGlobalIlluminationFlags.EmissiveIsBlack;
                    mat.SetFloat("_EnvironmentReflections", 1f);
                    mat.SetFloat("_SpecularHighlights", 1f);
                }
                bool cutout = d.shader == "litCutout" || d.shader == "unlitCutout";
                bool additive = d.shader == "unlitAdditive" || d.shader == "particlesAdditive";
                bool particles = d.shader.StartsWith("particles");
                bool transparent = d.shader == "unlitTransparent" || additive;
                mat.SetFloat("_AlphaClip", cutout ? 1f : 0f);
                mat.SetFloat("_Cutoff", cutout ? d.cutoff : 0.5f);
                mat.SetFloat("_Surface", transparent ? 1f : 0f);
                mat.SetFloat("_Blend", additive ? 2f : 0f);
                mat.SetFloat("_Cull", d.doubleSided || particles ? 0f : 2f);
                mat.SetFloat("_ReceiveShadows", transparent ? 0f : 1f);
                if (lit) BaseShaderGUI.SetMaterialKeywords(mat, LitGUI.SetMaterialKeywords);
                else if (particles) BaseShaderGUI.SetMaterialKeywords(mat, null, ParticleGUI.SetMaterialKeywords);
                else BaseShaderGUI.SetMaterialKeywords(mat);
                if (transparent) mat.renderQueue = 3000;
                else if (cutout) mat.renderQueue = 2450;
            }

            if (created) AssetDatabase.CreateAsset(mat, path);
            else EditorUtility.SetDirty(mat);
        }
    }
}
