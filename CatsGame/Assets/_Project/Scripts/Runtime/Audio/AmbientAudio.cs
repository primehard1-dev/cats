using UnityEngine;

namespace Cats
{
    /// <summary>
    /// The night soundscape: crickets and wind everywhere, the sea getting louder as the cat
    /// goes down towards the harbour, a church bell striking midnight after the intro.
    /// Positional sounds (café music, lantern hum) are separate 3D AudioSources in the scene.
    /// </summary>
    public class AmbientAudio : MonoBehaviour
    {
        public AudioClip sea, crickets, wind, bell;
        public Transform listener;
        public Transform bellTower;
        [Tooltip("Z (along the street) where the sea is loudest.")]
        public float seaZ = 92f;
        public float firstBellDelay = 4f;
        public int midnightStrokes = 3;
        public Vector2 bellInterval = new Vector2(110f, 160f);

        AudioSource _sea, _crickets, _wind, _bell;
        float _nextBell;
        int _strokesLeft;

        AudioSource Loop(AudioClip clip, float volume)
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.clip = clip;
            s.loop = true;
            s.volume = volume;
            s.spatialBlend = 0f;
            s.playOnAwake = false;
            if (clip != null) s.Play();
            return s;
        }

        void Start()
        {
            _sea = Loop(sea, 0.25f);
            _crickets = Loop(crickets, 0.22f);
            _wind = Loop(wind, 0.18f);
            if (bellTower != null)
            {
                _bell = bellTower.gameObject.AddComponent<AudioSource>();
                _bell.spatialBlend = 0.85f;
                _bell.rolloffMode = AudioRolloffMode.Linear;
                _bell.minDistance = 50f;
                _bell.maxDistance = 900f;
                _bell.dopplerLevel = 0f;
            }
            _strokesLeft = midnightStrokes;
            _nextBell = Time.time + firstBellDelay;
        }

        void Update()
        {
            if (listener != null && _sea != null)
            {
                float k = Mathf.InverseLerp(seaZ - 90f, seaZ, listener.position.z);
                _sea.volume = Mathf.Lerp(0.22f, 0.75f, k * k);
                _crickets.volume = Mathf.Lerp(0.24f, 0.12f, k);
            }
            if (_bell != null && bell != null && Time.time >= _nextBell)
            {
                _bell.PlayOneShot(bell, 1f);
                if (_strokesLeft > 1) { _strokesLeft--; _nextBell = Time.time + 2.6f; }
                else { _strokesLeft = 1; _nextBell = Time.time + Random.Range(bellInterval.x, bellInterval.y); }
            }
        }
    }
}
