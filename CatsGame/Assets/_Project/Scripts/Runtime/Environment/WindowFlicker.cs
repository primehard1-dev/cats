using UnityEngine;

namespace Cats
{
    /// <summary>Someone is watching TV: a bluish flickering light from a window onto the street.</summary>
    [RequireComponent(typeof(Light))]
    public class WindowFlicker : MonoBehaviour
    {
        public Color a = new Color(0.55f, 0.65f, 1f);
        public Color b = new Color(0.9f, 0.85f, 1f);
        public float intensity = 1.2f;
        Light _l;
        float _next, _target = 1f, _level = 1f;

        void Start()
        {
            _l = GetComponent<Light>();
            if (!QualityTier.IsHigh) _l.enabled = false;
        }

        void Update()
        {
            if (Time.time > _next)
            {
                _target = Random.Range(0.35f, 1.1f);
                _l.color = Color.Lerp(a, b, Random.value);
                _next = Time.time + Random.Range(0.06f, 0.4f);
            }
            _level = Mathf.Lerp(_level, _target, Time.deltaTime * 25f);
            _l.intensity = intensity * _level;
        }
    }
}
