using UnityEditor;
using UnityEngine;

namespace Cats.EditorTools
{
    /// <summary>Import settings for the generated textures and Blender models (by file name convention).</summary>
    public class CatsAssetPostprocessor : AssetPostprocessor
    {
        void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith(CatsPaths.Textures)) return;
            var ti = (TextureImporter)assetImporter;
            string file = System.IO.Path.GetFileNameWithoutExtension(assetPath);
            var android = new TextureImporterPlatformSettings { name = "Android", overridden = true, format = TextureImporterFormat.ASTC_6x6 };
            ti.maxTextureSize = 2048;
            ti.mipmapEnabled = true;
            ti.wrapMode = TextureWrapMode.Repeat;
            ti.anisoLevel = 2;
            ti.textureCompression = TextureImporterCompression.CompressedHQ;

            if (file.StartsWith("UI_"))
            {
                ti.textureType = TextureImporterType.Sprite;
                ti.spriteImportMode = SpriteImportMode.Single;
                ti.alphaIsTransparency = true;
                ti.mipmapEnabled = false;
                ti.wrapMode = TextureWrapMode.Clamp;
                ti.maxTextureSize = 512;
                android.format = TextureImporterFormat.ASTC_4x4;
            }
            else if (file.EndsWith("_N"))
            {
                ti.textureType = TextureImporterType.NormalMap;
            }
            else if (file.EndsWith("_M"))
            {
                ti.textureType = TextureImporterType.Default;
                ti.sRGBTexture = false;
            }
            else
            {
                ti.textureType = TextureImporterType.Default;
                ti.sRGBTexture = true;
                ti.alphaIsTransparency = file.Contains("Foliage") || file.Contains("Palm") || file.Contains("Matte") ||
                                         file.Contains("Moon") || file.Contains("Paw");
            }

            if (file == "T_SkyNight_A")
            {
                ti.maxTextureSize = 4096;
                ti.mipmapEnabled = false;
                ti.wrapModeU = TextureWrapMode.Repeat;
                ti.wrapModeV = TextureWrapMode.Clamp;
            }
            else if (file == "T_FarMatte_A")
            {
                ti.maxTextureSize = 4096;
                ti.wrapMode = TextureWrapMode.Clamp;
            }
            else if (file.Contains("Moon") || file.Contains("Paw"))
            {
                ti.wrapMode = TextureWrapMode.Clamp;
            }
            if (file.Contains("TerraceTiles") || file.Contains("Cobble") || file.Contains("RoofTiles")) ti.anisoLevel = 4;
            android.maxTextureSize = ti.maxTextureSize;
            ti.SetPlatformTextureSettings(android);
        }

        void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith(CatsPaths.Root + "/Audio")) return;
            var ai = (AudioImporter)assetImporter;
            string file = System.IO.Path.GetFileNameWithoutExtension(assetPath);
            bool longClip = file.StartsWith("amb_") || file.StartsWith("mus_");
            ai.forceToMono = true;
            ai.loadInBackground = longClip;
            var s = ai.defaultSampleSettings;
            s.compressionFormat = AudioCompressionFormat.Vorbis;
            s.quality = longClip ? 0.5f : 0.7f;
            s.loadType = longClip ? AudioClipLoadType.CompressedInMemory : AudioClipLoadType.DecompressOnLoad;
            ai.defaultSampleSettings = s;
        }

        void OnPreprocessModel()
        {
            if (!assetPath.StartsWith(CatsPaths.Models)) return;
            var mi = (ModelImporter)assetImporter;
            string file = System.IO.Path.GetFileNameWithoutExtension(assetPath);
            mi.globalScale = 1f;
            mi.useFileScale = true;
            mi.bakeAxisConversion = true;
            mi.importAnimation = false;
            mi.importCameras = false;
            mi.importLights = false;
            mi.importBlendShapes = false;
            mi.animationType = ModelImporterAnimationType.None;
            mi.importNormals = ModelImporterNormals.Import;
            mi.isReadable = false;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
            bool dynamicModel = file.StartsWith("Cat_") || file == "Ship" || file == "Bulb";
            mi.generateSecondaryUV = !dynamicModel;
            mi.secondaryUVHardAngle = 70f;
            mi.secondaryUVPackMargin = 8f;
        }
    }
}
