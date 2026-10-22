using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Cats
{
    /// <summary>
    /// Level flow: intro fade, checkpoints, respawn, hints, level end.
    /// Players are kept in a list so a second cat (co-op over a phone hotspot) only needs another slot.
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

        public List<PlayerSlot> players = new List<PlayerSlot>();
        public Transform player2Spawn;
        public GameUI ui;
        [TextArea] public string startHint = "Джойстик слева — идти, кнопка справа — прыжок. Прыгай туда, где светятся лапки.";

        readonly HashSet<string> _shownHints = new HashSet<string>();
        readonly HashSet<CatController> _respawning = new HashSet<CatController>();
        float _startTime;
        bool _finished;

        void Awake()
        {
            Instance = this;
            QualityTier.Apply();
            foreach (var p in players)
            {
                if (p.cat == null) continue;
                p.startPosition = p.cat.transform.position;
                p.startYaw = p.cat.transform.eulerAngles.y;
            }
        }

        IEnumerator Start()
        {
            _startTime = Time.time;
            foreach (var p in players) if (p.cat != null) p.cat.SetFrozen(true);
            if (ui != null) ui.FadeTo(0f, 1.6f);
            yield return new WaitForSeconds(1.2f);
            foreach (var p in players) if (p.cat != null) p.cat.SetFrozen(false);
            ShowHintOnce(startHint, 6f);
        }

        PlayerSlot Slot(CatController cat) => players.Find(p => p.cat == cat);

        public void ReachCheckpoint(CatController cat, Checkpoint cp)
        {
            var slot = Slot(cat);
            if (slot == null || slot.checkpoint == cp) return;
            slot.checkpoint = cp;
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
            foreach (var p in players) if (p.cat != null) p.cat.SetFrozen(true);
            if (ui != null)
                ui.ShowFinish($"Уровень 1 пройден!\nЛунная улица — {Mathf.FloorToInt(t / 60f)}:{Mathf.FloorToInt(t % 60f):00}");
        }
    }
}
