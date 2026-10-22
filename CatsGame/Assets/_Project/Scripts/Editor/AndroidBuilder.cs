using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Cats.EditorTools
{
    /// <summary>
    /// One-click Android build: generates the scenes if they are missing, bakes the light if it was never baked,
    /// switches to Android and writes Builds/CatsMoonStreet.apk.
    /// Also callable from the command line: -batchmode -executeMethod Cats.EditorTools.AndroidBuilder.BuildBatch
    /// (add -catsSkipBake to build without baking, e.g. for a quick CI check).
    /// </summary>
    public static class AndroidBuilder
    {
        const string ApkPath = "Builds/CatsMoonStreet.apk";

        [MenuItem("Cats/6. Build APK for phone", priority = 80)]
        static void BuildFromMenu()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (Build()) EditorUtility.RevealInFinder(ApkPath);
        }

        public static void BuildBatch() => EditorApplication.Exit(Build() ? 0 : 1);

        static bool Build()
        {
            if (!File.Exists(CatsPaths.Level01Scene) || !File.Exists(CatsPaths.MainMenuScene))
            {
                ProjectSetup.Run();
                MaterialLibrary.BuildAll();
                PrefabFactory.BuildAll();
                MenuBuilder.Build();
                Level01Builder.Build();
            }

            EditorSceneManager.OpenScene(CatsPaths.Level01Scene);
            bool skipBake = System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-catsSkipBake") >= 0;
            if (Lightmapping.lightingDataAsset == null && !skipBake)
            {
                Debug.Log("[Cats] Level was never baked, baking now (this takes a while)…");
                Lightmapping.lightingSettings = LightingSetup.GetOrCreate();
                if (!Lightmapping.Bake()) Debug.LogWarning("[Cats] Bake failed or was cancelled, building without baked light.");
                EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
            }

            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android &&
                !EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android))
            {
                Debug.LogError("[Cats] Could not switch to Android. Is Android Build Support installed (Unity Hub → Installs → Add modules)?");
                return false;
            }

            CatsMenu.UpdateBuildScenes();
            Directory.CreateDirectory(Path.GetDirectoryName(ApkPath));
            EditorUserBuildSettings.buildAppBundle = false;
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { CatsPaths.MainMenuScene, CatsPaths.Level01Scene },
                locationPathName = ApkPath,
                target = BuildTarget.Android,
                options = BuildOptions.None,
            });
            bool ok = report.summary.result == BuildResult.Succeeded;
            if (ok) Debug.Log($"[Cats] APK ready: {Path.GetFullPath(ApkPath)} ({report.summary.totalSize / (1024 * 1024)} MB)");
            else Debug.LogError($"[Cats] Android build failed: {report.summary.result}, {report.summary.totalErrors} errors. See the Console above.");
            return ok;
        }
    }
}
