using UnityEditor;
using UnityEditor.SceneManagement;

namespace Cats.EditorTools
{
    public static class CatsMenu
    {
        [MenuItem("Cats/0. Do everything (1-3)", priority = 0)]
        static void All()
        {
            ProjectSetup.Run();
            MaterialLibrary.BuildAll();
            PrefabFactory.BuildAll();
            Level01Builder.Build();
        }

        [MenuItem("Cats/1. Configure project (Android, URP)", priority = 20)]
        static void Setup() => ProjectSetup.Run();

        [MenuItem("Cats/2. Build materials and prefabs", priority = 21)]
        static void Assets()
        {
            MaterialLibrary.BuildAll();
            PrefabFactory.BuildAll();
        }

        [MenuItem("Cats/3. Build level 01 scene", priority = 22)]
        static void Level() => Level01Builder.Build();

        [MenuItem("Cats/4. Bake lighting", priority = 40)]
        static void Bake()
        {
            if (EditorSceneManager.GetActiveScene().path != CatsPaths.Level01Scene)
                EditorSceneManager.OpenScene(CatsPaths.Level01Scene);
            LightingSetup.Bake();
        }
    }
}
