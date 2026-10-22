using UnityEngine;
using UnityEngine.UI;

namespace Cats
{
    /// <summary>Fade overlay, hints, dialogue box, "saved" badge, pause menu and finish panel.</summary>
    public class GameUI : MonoBehaviour
    {
        public CanvasGroup fade;
        public Text hintText;
        public CanvasGroup hintGroup;
        public Text dialogueName;
        public Text dialogueText;
        public CanvasGroup dialogueGroup;
        public CanvasGroup finishGroup;
        public Text finishText;
        public Button finishMenuButton;
        public Button finishRetryButton;
        public GameObject touchControls;
        public CanvasGroup savedGroup;

        [Header("Pause")]
        public Button pauseButton;
        public GameObject pausePanel;
        public Button resumeButton;
        public Button settingsButton;
        public Button restartButton;
        public Button menuButton;
        public SettingsPanel settings;
        public AudioClip tap;

        float _hintUntil, _dialogueUntil, _savedUntil, _fadeTarget, _fadeSpeed = 2f;

        void Awake()
        {
            if (fade != null) fade.alpha = 1f;
            if (hintGroup != null) hintGroup.alpha = 0f;
            if (dialogueGroup != null) dialogueGroup.alpha = 0f;
            if (savedGroup != null) savedGroup.alpha = 0f;
            if (finishGroup != null) { finishGroup.alpha = 0f; finishGroup.gameObject.SetActive(false); }
            if (pausePanel != null) pausePanel.SetActive(false);
            if (settings != null) settings.gameObject.SetActive(false);
        }

        public void Bind(GameManager gm)
        {
            void On(Button b, System.Action a)
            {
                if (b != null) b.onClick.AddListener(() => { gm.PlayTap(); a(); });
            }
            On(pauseButton, () => gm.SetPaused(true));
            On(resumeButton, () => gm.SetPaused(false));
            On(restartButton, gm.RestartLevel);
            On(menuButton, gm.GoToMenu);
            On(finishMenuButton, gm.GoToMenu);
            On(finishRetryButton, gm.RestartLevel);
            On(settingsButton, () =>
            {
                pausePanel.SetActive(false);
                settings.gameObject.SetActive(true);
            });
            if (settings != null) settings.onClosed = () => { if (gm.Paused) pausePanel.SetActive(true); };
        }

        public void FadeTo(float alpha, float seconds)
        {
            _fadeTarget = alpha;
            _fadeSpeed = 1f / Mathf.Max(0.01f, seconds);
        }

        public bool FadeDone => fade == null || Mathf.Approximately(fade.alpha, _fadeTarget);

        public void ShowHint(string text, float seconds)
        {
            if (hintText == null) return;
            hintText.text = text;
            _hintUntil = Time.time + seconds;
        }

        public void ShowDialogue(string speaker, string text, float seconds)
        {
            if (dialogueText == null) return;
            if (dialogueName != null) dialogueName.text = speaker;
            dialogueText.text = text;
            _dialogueUntil = Time.time + seconds;
        }

        public void ShowSaved() => _savedUntil = Time.time + 2f;

        public void ShowPause(bool paused)
        {
            if (pausePanel != null) pausePanel.SetActive(paused);
            if (!paused && settings != null && settings.gameObject.activeSelf) settings.Close();
            if (touchControls != null) touchControls.SetActive(!paused);
            if (pauseButton != null) pauseButton.gameObject.SetActive(!paused);
        }

        public void ShowFinish(string text)
        {
            if (finishText != null) finishText.text = text;
            if (finishGroup != null)
            {
                finishGroup.gameObject.SetActive(true);
                finishGroup.alpha = 1f;
                finishGroup.blocksRaycasts = true;
                finishGroup.interactable = true;
            }
            if (touchControls != null) touchControls.SetActive(false);
            if (pauseButton != null) pauseButton.gameObject.SetActive(false);
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            if (fade != null) fade.alpha = Mathf.MoveTowards(fade.alpha, _fadeTarget, _fadeSpeed * dt);
            if (hintGroup != null) hintGroup.alpha = Mathf.MoveTowards(hintGroup.alpha, Time.time < _hintUntil ? 1f : 0f, dt * 3f);
            if (dialogueGroup != null)
                dialogueGroup.alpha = Mathf.MoveTowards(dialogueGroup.alpha, Time.time < _dialogueUntil ? 1f : 0f, dt * 4f);
            if (savedGroup != null) savedGroup.alpha = Mathf.MoveTowards(savedGroup.alpha, Time.time < _savedUntil ? 1f : 0f, dt * 3f);
        }
    }
}
