using System.Collections.Generic;
using UnityEngine;

namespace Cats
{
    /// <summary>Glowing paw: a jump target. The cat's jump button lands exactly on it.</summary>
    public class JumpMarker : MonoBehaviour
    {
        public static readonly List<JumpMarker> All = new List<JumpMarker>();

        public float pulsePeriod = 1.5f;
        public Renderer pawRenderer;

        MaterialPropertyBlock _mpb;
        Color _baseColor;
        static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");

        public Vector3 LandingPoint => transform.position;

        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        void Start()
        {
            if (pawRenderer == null) pawRenderer = GetComponentInChildren<Renderer>();
            if (pawRenderer != null)
            {
                _mpb = new MaterialPropertyBlock();
                _baseColor = pawRenderer.sharedMaterial.GetColor(BaseColorId);
            }
        }

        void Update()
        {
            if (_mpb == null) return;
            float k = 0.65f + 0.35f * Mathf.Sin(Time.time * Mathf.PI * 2f / pulsePeriod);
            var c = _baseColor * k;
            c.a = _baseColor.a * (0.6f + 0.4f * k);
            _mpb.SetColor(BaseColorId, c);
            pawRenderer.SetPropertyBlock(_mpb);
        }
    }
}
