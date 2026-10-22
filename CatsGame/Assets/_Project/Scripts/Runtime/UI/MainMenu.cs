using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using UnityEngine.Video;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Cats
{
    /// <summary>
    /// Main menu over the living-photo loop of the reference picture:
    /// Continue / New game / Settings / About / Quit, fade into the level.
    /// </summary>
    public class MainMenu : MonoBehaviour
    {
        public VideoPlayer video;
        public RawImage background;
        public Texture poster;
        public RenderTexture videoTarget;

        public GameObject mainPanel;
        public Button continueButton;
        public Text continueLabel;
        public Button newGameButton;
        public Button settingsButton;
        public Button aboutButton;
        public Button quitButton;
        public SettingsPanel settings;
        public GameObject aboutPanel;
        public Button aboutBack;
        public Text recordText;

        public CanvasGroup fade;
        public Text loadingText;
        public AudioSource uiAudio;
        public AudioClip tap;
        public string levelScene = "Level01_MoonStreet";

        bool _loading;

        static readonly string[] CheckpointNames =
        {
            "B1", "у Барона", "LedgeEnd", "в конце карниза", "B2", "на нижнем балконе", "B3", "за гирляндой",
            "R1", "на крыше с бельём", "Cafe", "у кафе", "Stairs", "у лестницы к морю",
        };

        void Start()
        {
            QualityTier.Apply();
            Time.timeScale = 1f;
            AudioListener.pause = false;
            if (background != null && poster != null) background.texture = poster;
            if (video != null)
            {
                video.prepareCompleted += v =>
                {
                    if (background != null && videoTarget != null) background.texture = videoTarget;
                    v.Play();
                };
                video.Prepare();
            }
            var data = SaveSystem.Data;
            continueButton.gameObject.SetActive(data.HasProgress);
            if (data.HasProgress && continueLabel != null)
                continueLabel.text = "Продолжить — " + CheckpointName(data.checkpoint);
            var rec = data.Record("Level01");
            if (recordText != null)
                recordText.text = rec.completed ? $"Лунная улица пройдена · рекорд {Mathf.FloorToInt(rec.bestTime / 60f)}:{Mathf.FloorToInt(rec.bestTime % 60f):00}" : "";

            continueButton.onClick.AddListener(() => { Tap(); StartLevel(true); });
            newGameButton.onClick.AddListener(() => { Tap(); SaveSystem.NewGame(); StartLevel(false); });
            settingsButton.onClick.AddListener(() => { Tap(); Show(settings.gameObject); });
            aboutButton.onClick.AddListener(() => { Tap(); Show(aboutPanel); });
            aboutBack.onClick.AddListener(() => { Tap(); Show(mainPanel); });
            quitButton.onClick.AddListener(() => { Tap(); Application.Quit(); });
            settings.onClosed = () => mainPanel.SetActive(true);
            Show(mainPanel);
            if (loadingText != null) loadingText.gameObject.SetActive(false);
            StartCoroutine(Fade(1f, 0f, 1.2f));
        }

        static string CheckpointName(string id)
        {
            if (string.IsNullOrEmpty(id)) return "с начала";
            for (int i = 0; i < CheckpointNames.Length; i += 2)
                if (CheckpointNames[i] == id) return CheckpointNames[i + 1];
            return id;
        }

        void Show(GameObject panel)
        {
            mainPanel.SetActive(panel == mainPanel);
            settings.gameObject.SetActive(panel == settings.gameObject);
            aboutPanel.SetActive(panel == aboutPanel);
        }

        void Tap()
        {
            if (uiAudio != null && tap != null) uiAudio.PlayOneShot(tap, 0.6f * CatsVolume.Sfx);
        }

        void Update()
        {
            if (_loading || !BackPressed()) return;
            if (settings.gameObject.activeSelf) settings.Close();
            else if (aboutPanel.activeSelf) Show(mainPanel);
            else Application.Quit();
        }

        static bool BackPressed()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.Escape);
#endif
        }

        void StartLevel(bool resume)
        {
            if (_loading) return;
            _loading = true;
            SaveSystem.ContinueRequested = resume;
            StartCoroutine(LoadRoutine());
        }

        IEnumerator LoadRoutine()
        {
            yield return Fade(0f, 1f, 0.7f);
            if (loadingText != null)
            {
                loadingText.gameObject.SetActive(true);
                loadingText.text = "Кот выходит на прогулку…";
            }
            var op = SceneManager.LoadSceneAsync(levelScene);
            while (!op.isDone) yield return null;
        }

        IEnumerator Fade(float from, float to, float seconds)
        {
            if (fade == null) yield break;
            fade.blocksRaycasts = true;
            for (float t = 0f; t < seconds; t += Time.unscaledDeltaTime)
            {
                fade.alpha = Mathf.Lerp(from, to, t / seconds);
                yield return null;
            }
            fade.alpha = to;
            fade.blocksRaycasts = to > 0.5f;
        }
    }
}
