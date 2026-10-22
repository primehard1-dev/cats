using UnityEngine;

namespace Cats
{
    /// <summary>Wet paw prints on the rain-soaked tiles and cobbles; they fade out after a few seconds.</summary>
    [RequireComponent(typeof(CatController))]
    public class CatFootprints : MonoBehaviour
    {
        public Material printMaterial;
        public Mesh quad;
        public int poolSize = 48;
        public float spacing = 0.13f;
        public float lifetime = 7f;
        [Tooltip("Material names (substring) of surfaces that keep prints.")]
        public string[] wetSurfaces = { "TerraceTiles", "Cobble", "Stone" };

        CatController _cat;
        Transform[] _prints;
        float[] _born;
        MaterialPropertyBlock _mpb;
        Renderer[] _renderers;
        int _next;
        float _travel;
        bool _left;
        Vector3 _last;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

        void Start()
        {
            _cat = GetComponent<CatController>();
            _mpb = new MaterialPropertyBlock();
            var root = new GameObject("Footprints").transform;
            _prints = new Transform[poolSize];
            _born = new float[poolSize];
            _renderers = new Renderer[poolSize];
            for (int i = 0; i < poolSize; i++)
            {
                var go = new GameObject("Print");
                go.transform.SetParent(root, false);
                go.AddComponent<MeshFilter>().sharedMesh = quad;
                var r = go.AddComponent<MeshRenderer>();
                r.sharedMaterial = printMaterial;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                r.enabled = false;
                _renderers[i] = r;
                _prints[i] = go.transform;
                _born[i] = -100f;
            }
            _last = transform.position;
        }

        bool IsWet(Collider c)
        {
            if (c == null) return false;
            var r = c.GetComponent<Renderer>();
            if (r == null || r.sharedMaterial == null) return false;
            var n = r.sharedMaterial.name;
            foreach (var w in wetSurfaces) if (n.Contains(w)) return true;
            return false;
        }

        void Update()
        {
            var pos = transform.position;
            var d = pos - _last;
            d.y = 0f;
            _last = pos;
            if (_cat.IsGrounded && _cat.CurrentState == CatController.State.Normal && IsWet(_cat.Ground))
            {
                _travel += d.magnitude;
                if (_travel > spacing)
                {
                    _travel = 0f;
                    _left = !_left;
                    var side = transform.right * (_left ? -0.04f : 0.04f);
                    var t = _prints[_next];
                    t.position = pos + side + Vector3.up * 0.006f;
                    t.rotation = Quaternion.LookRotation(Vector3.down, transform.forward);
                    t.localScale = Vector3.one * 0.07f;
                    _renderers[_next].enabled = true;
                    _born[_next] = Time.time;
                    _next = (_next + 1) % poolSize;
                }
            }
            for (int i = 0; i < poolSize; i++)
            {
                if (!_renderers[i].enabled) continue;
                float age = Time.time - _born[i];
                if (age > lifetime) { _renderers[i].enabled = false; continue; }
                _mpb.SetColor(BaseColor, new Color(1f, 1f, 1f, 0.55f * (1f - age / lifetime)));
                _renderers[i].SetPropertyBlock(_mpb);
            }
        }
    }
}
