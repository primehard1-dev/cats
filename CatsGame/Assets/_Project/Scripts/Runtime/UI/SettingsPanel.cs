using UnityEngine;
using UnityEngine.UI;

namespace Cats
{
    /// <summary>Settings shared by the main menu and the pause menu: volumes, quality, camera.</summary>
    public class SettingsPanel : MonoBehaviour
    {
        public Slider music;
        public Slider sfx;
        public Slider sensitivity;
        public Button qualityButton;
        public Text qualityLabel;
        public Button invertButton;
        public Text invertLabel;
        public Button backButton;
        public System.Action onClosed;

        static readonly string[] QualityNames = { "Качество: авто", "Качество: экономно", "Качество: красиво" };
        bool _loading;

        void Awake()
        {
            music.onValueChanged.AddListener(v => { if (!_loading) SaveSystem.Settings.musicVolume = v; });
            sfx.onValueChanged.AddListener(v => { if (!_loading) SaveSystem.Settings.sfxVolume = v; });
            sensitivity.onValueChanged.AddListener(v => { if (!_loading) SaveSystem.Settings.lookSensitivity = v; });
            qualityButton.onClick.AddListener(() =>
            {
                var s = SaveSystem.Settings;
                s.quality = (s.quality + 1) % 3;
                QualityTier.Apply();
                Refresh();
            });
            invertButton.onClick.AddListener(() =>
            {
                SaveSystem.Settings.invertY = !SaveSystem.Settings.invertY;
                Refresh();
            });
            backButton.onClick.AddListener(Close);
        }

        void OnEnable()
        {
            _loading = true;
            var s = SaveSystem.Settings;
            music.value = s.musicVolume;
            sfx.value = s.sfxVolume;
            sensitivity.value = s.lookSensitivity;
            _loading = false;
            Refresh();
        }

        void Refresh()
        {
            var s = SaveSystem.Settings;
            qualityLabel.text = QualityNames[Mathf.Clamp(s.quality, 0, 2)];
            invertLabel.text = s.invertY ? "Камера: инверсия по вертикали" : "Камера: обычная";
        }

        public void Close()
        {
            SaveSystem.Save();
            gameObject.SetActive(false);
            onClosed?.Invoke();
        }
    }
}
