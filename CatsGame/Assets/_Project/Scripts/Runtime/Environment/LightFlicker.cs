using UnityEngine;

namespace Cats
{
    /// <summary>Very subtle candle-like flicker for real-time / mixed lanterns.</summary>
    [RequireComponent(typeof(Light))]
    public class LightFlicker : MonoBehaviour
    {
        public float amount = 0.06f;
        public float speed = 3f;
        Light _light;
        float _base, _seed;

        void Start()
        {
            _light = GetComponent<Light>();
            _base = _light.intensity;
            _seed = Random.value * 50f;
        }

        void Update()
        {
            _light.intensity = _base * (1f + (Mathf.PerlinNoise(Time.time * speed, _seed) - 0.5f) * 2f * amount);
        }
    }
}
