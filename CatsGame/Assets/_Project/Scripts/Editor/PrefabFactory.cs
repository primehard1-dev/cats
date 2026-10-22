using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace Cats.EditorTools
{
    /// <summary>Turns every Blender FBX in Art/Models into a prefab that uses the URP material library.</summary>
    public static class PrefabFactory
    {
        public static void BuildAll()
        {
            EditorUtil.EnsureFolder(CatsPaths.Prefabs);
            int count = 0;
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { CatsPaths.Models }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (model == null) continue;
                var inst = Object.Instantiate(model);
                inst.name = model.name;
                ApplyLibraryMaterials(inst);
                foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>())
                {
                    smr.quality = SkinQuality.Bone2;
                    smr.updateWhenOffscreen = false;
                }
                foreach (var anim in inst.GetComponentsInChildren<Animator>()) Object.DestroyImmediate(anim);
                foreach (var r in inst.GetComponentsInChildren<Renderer>())
                {
                    r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                    if (inst.name == "Bulb") r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                }
                PrefabUtility.SaveAsPrefabAsset(inst, $"{CatsPaths.Prefabs}/{model.name}.prefab");
                Object.DestroyImmediate(inst);
                count++;
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[Cats] {count} prefabs ready in {CatsPaths.Prefabs}");
        }

        public static GameObject Load(string name) => AssetDatabase.LoadAssetAtPath<GameObject>($"{CatsPaths.Prefabs}/{name}.prefab");

        /// <summary>Replaces the FBX's placeholder materials with library materials of the same name.</summary>
        public static void ApplyLibraryMaterials(GameObject go)
        {
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null) continue;
                    var lib = MaterialLibrary.Get(CleanName(mats[i].name));
                    if (lib != null) mats[i] = lib;
                }
                r.sharedMaterials = mats;
            }
        }

        /// <summary>"M_AwningBlue=M_AwningGreen" swaps one material on an instance.</summary>
        public static void SwapMaterials(GameObject go, string swap)
        {
            if (string.IsNullOrEmpty(swap) || !swap.Contains("=")) return;
            var parts = swap.Split('=');
            if (parts[0] == parts[1]) return;
            var to = MaterialLibrary.Get(parts[1]);
            if (to == null) return;
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                var mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] != null && CleanName(mats[i].name) == parts[0]) { mats[i] = to; changed = true; }
                }
                if (changed) r.sharedMaterials = mats;
            }
        }

        static string CleanName(string n)
        {
            int i = n.IndexOf(' ');
            n = i > 0 ? n.Substring(0, i) : n;
            int dot = n.IndexOf('.');
            return dot > 0 ? n.Substring(0, dot) : n;
        }

        public static readonly HashSet<string> SmallProps = new HashSet<string>
        {
            "FlowerBox_Red", "FlowerBox_White", "FlowerBox_Magenta", "Pot_Geranium", "Pot_Daisy", "Pot_Small",
            "Ivy_Patch", "Ivy_Tall", "Bougainvillea", "Drainpipe_1m", "Bulb", "Crate", "CafeTable", "CafeChair",
            "Laundry_Line", "Lantern_Wall", "Railing_Post", "Palm", "Cypress", "Planter_Stone", "Chimney", "StreetLamp",
        };
    }
}
