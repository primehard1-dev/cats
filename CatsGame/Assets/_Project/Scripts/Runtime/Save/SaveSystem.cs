using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Cats
{
    [Serializable]
    public class GameSettings
    {
        public float musicVolume = 0.8f;
        public float sfxVolume = 1f;
        [Tooltip("0 = auto, 1 = economy (Low), 2 = beautiful (High)")]
        public int quality;
        public float lookSensitivity = 1f;
        public bool invertY;
    }

    [Serializable]
    public class LevelRecord
    {
        public string id;
        public bool completed;
        public float bestTime;
    }

    [Serializable]
    public class SaveData
    {
        public int version = 1;
        public string level = "";
        public string checkpoint = "";
        public float playSeconds;
        public int meows;
        public int potsBroken;
        public List<LevelRecord> levels = new List<LevelRecord>();
        public GameSettings settings = new GameSettings();

        public bool HasProgress => !string.IsNullOrEmpty(level);

        public LevelRecord Record(string id)
        {
            var r = levels.Find(l => l.id == id);
            if (r == null) { r = new LevelRecord { id = id }; levels.Add(r); }
            return r;
        }
    }

    /// <summary>JSON save in Application.persistentDataPath: progress (checkpoint), records, settings.</summary>
    public static class SaveSystem
    {
        const string FileName = "cats_save.json";
        static SaveData _data;

        /// <summary>Set by the main menu: the level should start from the saved checkpoint.</summary>
        public static bool ContinueRequested;

        static string FilePath => Path.Combine(Application.persistentDataPath, FileName);

        public static SaveData Data
        {
            get
            {
                if (_data == null) Load();
                return _data;
            }
        }

        public static GameSettings Settings => Data.settings;

        public static void Load()
        {
            try
            {
                _data = File.Exists(FilePath) ? JsonUtility.FromJson<SaveData>(File.ReadAllText(FilePath)) : null;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[Cats] Save file unreadable, starting fresh: {e.Message}");
                _data = null;
            }
            if (_data == null) _data = new SaveData();
            if (_data.settings == null) _data.settings = new GameSettings();
        }

        public static void Save()
        {
            try
            {
                var tmp = FilePath + ".tmp";
                File.WriteAllText(tmp, JsonUtility.ToJson(Data, true));
                if (File.Exists(FilePath)) File.Delete(FilePath);
                File.Move(tmp, FilePath);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[Cats] Could not save: {e.Message}");
            }
        }

        /// <summary>Starts over but keeps settings and level records.</summary>
        public static void NewGame()
        {
            Data.level = "";
            Data.checkpoint = "";
            Save();
        }

        public static void SetCheckpoint(string level, string checkpoint)
        {
            Data.level = level;
            Data.checkpoint = checkpoint;
            Save();
        }

        public static void CompleteLevel(string level, float seconds)
        {
            var r = Data.Record(level);
            r.completed = true;
            if (r.bestTime <= 0f || seconds < r.bestTime) r.bestTime = seconds;
            Data.level = "";
            Data.checkpoint = "";
            Save();
        }
    }

    /// <summary>Volume multipliers from the settings (music & ambience / sound effects).</summary>
    public static class CatsVolume
    {
        public static float Music => SaveSystem.Settings.musicVolume;
        public static float Sfx => SaveSystem.Settings.sfxVolume;
    }
}
