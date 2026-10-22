using UnityEngine;

namespace Cats
{
    /// <summary>Scales an AudioSource by the music or sound-effects volume from the settings.</summary>
    [RequireComponent(typeof(AudioSource))]
    public class AudioVolume : MonoBehaviour
    {
        public enum Category { Music, Sfx }

        public Category category = Category.Music;
        AudioSource _src;
        float _base;

        void Awake()
        {
            _src = GetComponent<AudioSource>();
            _base = _src.volume;
        }

        void Update()
        {
            _src.volume = _base * (category == Category.Music ? CatsVolume.Music : CatsVolume.Sfx);
        }
    }
}
