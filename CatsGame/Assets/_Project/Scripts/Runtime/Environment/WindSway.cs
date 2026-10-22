using UnityEngine;

namespace Cats
{
    /// <summary>Night breeze: gently rocks laundry, garland bulbs, palms and cypresses (non-static objects only).</summary>
    public class WindSway : MonoBehaviour
    {
        public Vector3 axis = Vector3.forward;
        public float amplitude = 4f;
        public float speed = 0.6f;
        float _seed;
        Quaternion _rest;

        void Start()
        {
            _rest = transform.localRotation;
            _seed = Random.value * 100f;
        }

        void Update()
        {
            float t = Time.time * speed;
            float a = (Mathf.PerlinNoise(t, _seed) - 0.5f) * 2f * amplitude + Mathf.Sin(t * 2.3f + _seed) * amplitude * 0.25f;
            transform.localRotation = _rest * Quaternion.AngleAxis(a, axis);
        }
    }
}
