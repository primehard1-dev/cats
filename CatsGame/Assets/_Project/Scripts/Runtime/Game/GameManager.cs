using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Cats
{
    /// <summary>
    /// Level flow: intro fade, checkpoints (saved to disk), continue from the saved checkpoint, respawn,
    /// hints, pause menu, level end. Players are kept in a list so a second cat (co-op over a phone
    /// hotspot) only needs another slot.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        [System.Serializable]
        public class PlayerSlot
        {
            public CatController cat;
            public CatCameraRig rig;
            public Checkpoint checkpoint;
            [HideInInspector] public Vector3 startPosition;
            [HideInInspector] public float startYaw;
        }

        public static GameManager Instance { get; private set; }

        public string levelId = "Level01";
        public string menuScene = "MainMenu";
        public List<PlayerSlot> players = new List<PlayerSlot>();
        public Transform player2Spawn;
        public GameUI ui;
        public AudioClip checkpointChime;
        [TextArea] public string startHint = "Джойстик слева — идти, кнопка справа — прыжок. Прыгай туда, где светятся лапки.";

        readonly HashSet<string> _shownHints = new HashSet<string>();
        readonly HashSet<CatController> _respawning = new HashSet<CatController>();
        float _startTime;
        bool _finished, _paused;
        AudioSource _uiAudio;

        public bool Paused => _paused;

        void Awake()
        {
            Instance = this;
            Time.timeScale = 1f;
            AudioListener.pause = false;
            QualityTier.Apply();
            _uiAudio = gameObject.AddComponent<AudioSource>();
            _uiAudio.ignoreListenerPause = true;
            foreach (var p in players)
            {
                if (p.cat == null) continue;
                p.startPosition = p.cat.transform.position;
                p.startYaw = p.cat.transform.eulerAngles.y;
            }
            if (ui != null) ui.Bind(this);
        }

        IEnumerator Start()
        {
            _startTime = Time.time;
            foreach (var p in players) if (p.cat != null) p.cat.SetFrozen(true);
            bool resumed = TryResumeFromSave();
            if (ui != null) ui.FadeTo(0f, 1.6f);
            yield return new WaitForSeconds(1.2f);
            foreach (var p in players) if (p.cat != null) p.cat.SetFrozen(false);
            ShowHintOnce(resumed ? "С возвращением! Продолжаем прогулку." : startHint, resumed ? 3f : 6f);
        }

        bool TryResumeFromSave()
        {
            var data = SaveSystem.Data;
            bool resume = SaveSystem.ContinueRequested && data.level == levelId && !string.IsNullOrEmpty(data.checkpoint);
            SaveSystem.ContinueRequested = false;
            if (!resume || players.Count == 0 || players[0].cat == null) return false;
            foreach (var cp in FindCheckpoints())
            {
                if (cp.id != data.checkpoint) continue;
                var slot = players[0];
                slot.checkpoint = cp;
                slot.cat.Teleport(cp.SpawnPosition, cp.spawnYaw);
                slot.cat.SetFrozen(true);
                if (slot.rig != null) slot.rig.Snap();
                return true;
            }
            return false;
        }

        static Checkpoint[] FindCheckpoints()
        {
#if UNITY_2023_1_OR_NEWER
            return Object.FindObjectsByType<Checkpoint>(FindObjectsSortMode.None);
#else
            return Object.FindObjectsOfType<Checkpoint>();
#endif
        }

        void Update()
        {
            if (!_finished && BackPressed()) SetPaused(!_paused);
            if (!_paused) SaveSystem.Data.playSeconds += Time.unscaledDeltaTime;
        }

        static bool BackPressed()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.Escape);
#endif
        }

        void OnApplicationPause(bool paused)
        {
            if (paused)
            {
                SaveSystem.Save();
                if (!_finished) SetPaused(true);
            }
        }

        PlayerSlot Slot(CatController cat) => players.Find(p => p.cat == cat);

        public void ReachCheckpoint(CatController cat, Checkpoint cp)
        {
            var slot = Slot(cat);
            if (slot == null || slot.checkpoint == cp) return;
            slot.checkpoint = cp;
            SaveSystem.SetCheckpoint(levelId, cp.id);
            if (ui != null) ui.ShowSaved();
            if (checkpointChime != null) _uiAudio.PlayOneShot(checkpointChime, 0.5f * CatsVolume.Sfx);
        }

        public void Respawn(CatController cat)
        {
            if (_finished || _respawning.Contains(cat)) return;
            StartCoroutine(RespawnRoutine(cat));
        }

        IEnumerator RespawnRoutine(CatController cat)
        {
            _respawning.Add(cat);
            var slot = Slot(cat);
            cat.SetFrozen(true);
            if (ui != null) ui.FadeTo(1f, 0.35f);
            yield return new WaitForSeconds(0.4f);
            var pos = slot != null && slot.checkpoint != null ? slot.checkpoint.SpawnPosition : slot?.startPosition ?? cat.transform.position;
            float yaw = slot != null && slot.checkpoint != null ? slot.checkpoint.spawnYaw : slot?.startYaw ?? 0f;
            cat.Teleport(pos, yaw);
            cat.SetFrozen(true);
            if (slot != null && slot.rig != null) slot.rig.Snap();
            yield return new WaitForSeconds(0.15f);
            if (ui != null) ui.FadeTo(0f, 0.5f);
            ShowHintOnce("Ничего, кошки приземляются на лапы. Попробуй ещё раз!", 2.5f, false);
            cat.SetFrozen(false);
            _respawning.Remove(cat);
        }

        public void ShowHintOnce(string text, float seconds, bool once = true)
        {
            if (string.IsNullOrEmpty(text) || ui == null) return;
            if (once && !_shownHints.Add(text)) return;
            ui.ShowHint(text, seconds);
        }

        public void Say(string speaker, string line, float seconds)
        {
            if (ui != null) ui.ShowDialogue(speaker, line, seconds);
        }

        public void CompleteLevel(CatController cat)
        {
            if (_finished) return;
            _finished = true;
            float t = Time.time - _startTime;
            var rec = SaveSystem.Data.Record(levelId);
            bool record = rec.bestTime <= 0f || t < rec.bestTime;
            SaveSystem.CompleteLevel(levelId, t);
            foreach (var p in players) if (p.cat != null) p.cat.SetFrozen(true);
            if (ui != null)
                ui.ShowFinish($"Уровень 1 пройден!\nЛунная улица — {Mathf.FloorToInt(t / 60f)}:{Mathf.FloorToInt(t % 60f):00}" +
                              (record ? "\nНовый рекорд!" : ""));
        }

        // ------------------------------------------------------------------ pause / menu
        public void SetPaused(bool paused)
        {
            if (_finished && paused) return;
            _paused = paused;
            Time.timeScale = paused ? 0f : 1f;
            AudioListener.pause = paused;
            if (ui != null) ui.ShowPause(paused);
            if (paused) SaveSystem.Save();
        }

        public void PlayTap()
        {
            if (ui != null && ui.tap != null) _uiAudio.PlayOneShot(ui.tap, 0.6f * CatsVolume.Sfx);
        }

        public void RestartLevel()
        {
            Time.timeScale = 1f;
            AudioListener.pause = false;
            SaveSystem.ContinueRequested = false;
            SceneManager.LoadScene(SceneManager.GetActiveScene().name);
        }

        public void GoToMenu()
        {
            SaveSystem.Save();
            Time.timeScale = 1f;
            AudioListener.pause = false;
            SceneManager.LoadScene(menuScene);
        }
    }
}
