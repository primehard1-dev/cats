using UnityEngine;

namespace Cats
{
    /// <summary>The glittering moon path on the sea: a long strip on the water that always points from the viewer to the moon.</summary>
    public class MoonPath : MonoBehaviour
    {
        public Vector3 moonDirection = new Vector3(0.4f, 0.19f, 0.9f);
        public float seaLevel = -9.2f;
        public float startDistance = 140f;
        public float length = 1400f;
        public float width = 70f;
        public Vector2 scroll = new Vector2(0f, 0.02f);

        Material _mat;
        static readonly int BaseMap = Shader.PropertyToID("_BaseMap");

        void Start()
        {
            var r = GetComponent<Renderer>();
            if (r != null) _mat = r.material;
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            if (cam == null) return;
            var flat = new Vector3(moonDirection.x, 0f, moonDirection.z).normalized;
            var origin = cam.transform.position;
            var center = new Vector3(origin.x, seaLevel, origin.z) + flat * (startDistance + length * 0.5f);
            transform.SetPositionAndRotation(center, Quaternion.LookRotation(flat, Vector3.up));
            transform.localScale = new Vector3(width, 1f, length);
            if (_mat != null) _mat.SetTextureOffset(BaseMap, scroll * Time.time);
        }
    }
}
