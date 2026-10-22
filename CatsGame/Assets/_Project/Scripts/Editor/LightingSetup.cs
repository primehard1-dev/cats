using UnityEditor;
using UnityEngine;

namespace Cats.EditorTools
{
    /// <summary>Baked lighting tuned for mobile: shadowmask, non-directional lightmaps, ~12 texels/m.</summary>
    public static class LightingSetup
    {
        const string Path = CatsPaths.Settings + "/Lighting_Level01.lighting";

        public static LightingSettings GetOrCreate()
        {
            EditorUtil.EnsureFolder(CatsPaths.Settings);
            var ls = AssetDatabase.LoadAssetAtPath<LightingSettings>(Path);
            if (ls == null)
            {
                ls = new LightingSettings { name = "Lighting_Level01" };
                AssetDatabase.CreateAsset(ls, Path);
            }
            ls.bakedGI = true;
            ls.realtimeGI = false;
            ls.mixedBakeMode = MixedLightingMode.Shadowmask;
            ls.lightmapper = LightingSettings.Lightmapper.ProgressiveGPU;
            ls.lightmapResolution = 12f;
            ls.lightmapPadding = 4;
            ls.lightmapMaxSize = 2048;
            ls.directionalityMode = LightmapsMode.NonDirectional;
#if UNITY_2022_1_OR_NEWER
            ls.lightmapCompression = LightmapCompression.NormalQuality;
#else
            ls.compressLightmaps = true;
#endif
            ls.ao = true;
            ls.aoMaxDistance = 0.6f;
            ls.aoExponentDirect = 0f;
            ls.aoExponentIndirect = 1.2f;
            ls.directSampleCount = 32;
            ls.indirectSampleCount = 256;
            ls.environmentSampleCount = 256;
            ls.maxBounces = 2;
            ls.filteringMode = LightingSettings.FilterMode.Auto;
            EditorUtility.SetDirty(ls);
            AssetDatabase.SaveAssets();
            return ls;
        }

        public static void Bake()
        {
            Lightmapping.lightingSettings = GetOrCreate();
            if (!Lightmapping.BakeAsync()) Debug.LogError("[Cats] Could not start the bake (is the level scene open?)");
            else Debug.Log("[Cats] Baking lightmaps, light probes and reflection probes… progress is in the bottom-right corner.");
        }
    }
}
