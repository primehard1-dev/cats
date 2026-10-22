using UnityEngine;

namespace Cats
{
    /// <summary>Scrolls the sea normal map so the moon path shimmers.</summary>
    public class WaterScroller : MonoBehaviour
    {
        public Vector2 speed = new Vector2(0.004f, 0.0025f);
        static readonly int BaseMap = Shader.PropertyToID("_BaseMap");
        Material _mat;

        void Start()
        {
            var r = GetComponent<Renderer>();
            if (r != null) _mat = r.material;
        }

        void Update()
        {
            if (_mat != null) _mat.SetTextureOffset(BaseMap, speed * Time.time);
        }
    }
}
