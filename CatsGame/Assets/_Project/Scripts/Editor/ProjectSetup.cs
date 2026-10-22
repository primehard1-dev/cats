using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Cats.EditorTools
{
    /// <summary>One-time project configuration: Android landscape, linear colour, URP Low/High, layers.</summary>
    public static class ProjectSetup
    {
        public const string PlayerLayer = "Player";
        public const string CatOnlyLayer = "CatOnly";
        public const string FxLayer = "FX";

        public static void Run()
        {
            SetupPlayer();
            SetupLayers();
            SetupRenderPipeline();
            AssetDatabase.SaveAssets();
            Debug.Log("[Cats] Project configured: Android landscape, Linear, URP Low/High, layers.");
        }

        static void SetupPlayer()
        {
            PlayerSettings.companyName = "Primehard";
            PlayerSettings.productName = "Cats: Moon Street";
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
#if UNITY_2021_2_OR_NEWER
            PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Android, "com.primehard.cats");
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
#else
            PlayerSettings.SetApplicationIdentifier(BuildTargetGroup.Android, "com.primehard.cats");
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Android, ScriptingImplementation.IL2CPP);
#endif
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel28;
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.Vulkan, GraphicsDeviceType.OpenGLES3 });
        }

        static void SetupLayers()
        {
            var assets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset");
            if (assets == null || assets.Length == 0) return;
            var tm = new SerializedObject(assets[0]);
            var layers = tm.FindProperty("layers");
            EnsureLayer(layers, 8, PlayerLayer);
            EnsureLayer(layers, 9, CatOnlyLayer);
            EnsureLayer(layers, 10, FxLayer);
            tm.ApplyModifiedProperties();
        }

        static void EnsureLayer(SerializedProperty layers, int index, string name)
        {
            for (int i = 0; i < layers.arraySize; i++)
                if (layers.GetArrayElementAtIndex(i).stringValue == name) return;
            var p = layers.GetArrayElementAtIndex(index);
            if (string.IsNullOrEmpty(p.stringValue)) p.stringValue = name;
            else Debug.LogWarning($"[Cats] Layer slot {index} is used by '{p.stringValue}', add layer '{name}' manually.");
        }

        public static int Layer(string name)
        {
            int l = LayerMask.NameToLayer(name);
            return l < 0 ? 0 : l;
        }

        static void SetupRenderPipeline()
        {
            EditorUtil.EnsureFolder(CatsPaths.Settings);
            string rendererPath = CatsPaths.Settings + "/URP_Renderer.asset";
            var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(rendererPath);
            if (renderer == null)
            {
                renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                renderer.postProcessData = AssetDatabase.LoadAssetAtPath<PostProcessData>(
                    "Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset");
                AssetDatabase.CreateAsset(renderer, rendererPath);
            }
            renderer.renderingMode = RenderingMode.Forward;
            EditorUtility.SetDirty(renderer);

            var high = GetOrCreate(CatsPaths.Settings + "/URP_High.asset", renderer);
            high.renderScale = 1f;
            high.msaaSampleCount = 2;
            high.supportsHDR = true;
            high.shadowDistance = 45f;
            high.shadowCascadeCount = 2;
            high.mainLightShadowmapResolution = 2048;
            high.maxAdditionalLightsCount = 4;
            high.supportsCameraDepthTexture = false;
            high.supportsCameraOpaqueTexture = false;
            SetFields(high, softShadows: true, additionalShadows: true);

            var low = GetOrCreate(CatsPaths.Settings + "/URP_Low.asset", renderer);
            low.renderScale = 0.75f;
            low.upscalingFilter = UpscalingFilterSelection.FSR;
            low.msaaSampleCount = 1;
            low.supportsHDR = true;
            low.shadowDistance = 25f;
            low.shadowCascadeCount = 1;
            low.mainLightShadowmapResolution = 1024;
            low.maxAdditionalLightsCount = 2;
            low.supportsCameraDepthTexture = false;
            low.supportsCameraOpaqueTexture = false;
            SetFields(low, softShadows: false, additionalShadows: false);

            EditorUtility.SetDirty(high);
            EditorUtility.SetDirty(low);
#if UNITY_2021_2_OR_NEWER
            GraphicsSettings.defaultRenderPipeline = high;
#else
            GraphicsSettings.renderPipelineAsset = high;
#endif
            int count = QualitySettings.names.Length;
            int current = QualitySettings.GetQualityLevel();
            for (int i = 0; i < count; i++)
            {
                QualitySettings.SetQualityLevel(i, false);
                QualitySettings.renderPipeline = i < (count + 1) / 2 ? low : high;
                QualitySettings.shadowmaskMode = ShadowmaskMode.Shadowmask;
                QualitySettings.vSyncCount = 0;
            }
            QualitySettings.SetQualityLevel(count > 0 ? count - 1 : current, true);
        }

        static UniversalRenderPipelineAsset GetOrCreate(string path, ScriptableRendererData renderer)
        {
            var a = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(path);
            if (a != null) return a;
            a = UniversalRenderPipelineAsset.Create(renderer);
            AssetDatabase.CreateAsset(a, path);
            return a;
        }

        /// <summary>Settings that URP only exposes as serialized fields.</summary>
        static void SetFields(UniversalRenderPipelineAsset asset, bool softShadows, bool additionalShadows)
        {
            var so = new SerializedObject(asset);
            void SetBool(string field, bool value)
            {
                var p = so.FindProperty(field);
                if (p != null) p.boolValue = value;
                else Debug.LogWarning($"[Cats] URP field {field} not found (URP version changed?)");
            }
            SetBool("m_MainLightShadowsSupported", true);
            SetBool("m_SoftShadowsSupported", softShadows);
            SetBool("m_AdditionalLightShadowsSupported", additionalShadows);
            SetBool("m_MixedLightingSupported", true);
            SetBool("m_ReflectionProbeBlending", true);
            SetBool("m_ReflectionProbeBoxProjection", true);
            var mode = so.FindProperty("m_AdditionalLightsRenderingMode");
            if (mode != null) mode.intValue = (int)LightRenderingMode.PerPixel;
            so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
