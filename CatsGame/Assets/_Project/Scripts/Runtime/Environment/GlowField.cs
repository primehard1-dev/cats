using UnityEngine;

namespace Cats
{
    /// <summary>
    /// Soft halos around every lantern, window and garland bulb, drawn as one particle system
    /// (one draw call): the glow that makes the reference image feel warm and hazy.
    /// </summary>
    [RequireComponent(typeof(ParticleSystem))]
    public class GlowField : MonoBehaviour
    {
        public Vector3[] positions;
        public float[] sizes;
        public Color[] colors;
        public float flicker = 0.06f;

        ParticleSystem _ps;
        ParticleSystem.Particle[] _particles;
        float[] _seed;

        void Start()
        {
            _ps = GetComponent<ParticleSystem>();
            int n = positions?.Length ?? 0;
            var main = _ps.main;
            main.maxParticles = Mathf.Max(1, n);
            var ep = new ParticleSystem.EmitParams();
            for (int i = 0; i < n; i++)
            {
                ep.position = positions[i];
                ep.startSize = sizes != null && i < sizes.Length ? sizes[i] : 1f;
                ep.startColor = colors != null && i < colors.Length ? colors[i] : Color.white;
                ep.startLifetime = 1e6f;
                ep.velocity = Vector3.zero;
                _ps.Emit(ep, 1);
            }
            _particles = new ParticleSystem.Particle[n];
            _seed = new float[n];
            for (int i = 0; i < n; i++) _seed[i] = Random.value * 50f;
        }

        void LateUpdate()
        {
            if (_particles == null || flicker <= 0f) return;
            int n = _ps.GetParticles(_particles);
            float t = Time.time * 3f;
            for (int i = 0; i < n && i < _seed.Length; i++)
            {
                float k = 1f + (Mathf.PerlinNoise(t, _seed[i]) - 0.5f) * 2f * flicker;
                _particles[i].startSize = (sizes != null && i < sizes.Length ? sizes[i] : 1f) * k;
            }
            _ps.SetParticles(_particles, n);
        }
    }
}
