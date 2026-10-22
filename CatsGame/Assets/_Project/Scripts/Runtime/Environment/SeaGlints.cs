using UnityEngine;

namespace Cats
{
    /// <summary>
    /// Reflections of the shore lights on the sea: a sparkly strip on the water under every light,
    /// always stretched towards the camera, so it reads as the vertical light trails of the reference.
    /// All strips live in one dynamic mesh (one draw call).
    /// </summary>
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public class SeaGlints : MonoBehaviour
    {
        public Vector3[] lights;
        public float[] strength;
        public Transform[] movingLights;
        public float seaLevel = -9.25f;
        public float length = 45f;
        public float width = 2.2f;

        Mesh _mesh;
        Vector3[] _v;
        Vector2[] _uv;
        Color[] _c;
        int _count;

        void Start()
        {
            _count = (lights?.Length ?? 0) + (movingLights?.Length ?? 0);
            _mesh = new Mesh { name = "SeaGlints" };
            _mesh.MarkDynamic();
            _v = new Vector3[_count * 4];
            _uv = new Vector2[_count * 4];
            _c = new Color[_count * 4];
            var tris = new int[_count * 6];
            for (int i = 0; i < _count; i++)
            {
                int v = i * 4;
                _uv[v] = new Vector2(0, 1); _uv[v + 1] = new Vector2(1, 1); _uv[v + 2] = new Vector2(1, 0); _uv[v + 3] = new Vector2(0, 0);
                tris[i * 6] = v; tris[i * 6 + 1] = v + 1; tris[i * 6 + 2] = v + 2;
                tris[i * 6 + 3] = v; tris[i * 6 + 4] = v + 2; tris[i * 6 + 5] = v + 3;
                float s = strength != null && i < strength.Length ? strength[i] : 1f;
                for (int k = 0; k < 4; k++) _c[v + k] = new Color(s, s, s, 1f);
            }
            _mesh.vertices = _v;
            _mesh.uv = _uv;
            _mesh.colors = _c;
            _mesh.triangles = tris;
            _mesh.bounds = new Bounds(Vector3.zero, Vector3.one * 1e5f);
            GetComponent<MeshFilter>().sharedMesh = _mesh;
            transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            if (cam == null || _mesh == null) return;
            var eye = cam.transform.position;
            int n = lights?.Length ?? 0;
            for (int i = 0; i < _count; i++)
            {
                var p = i < n ? lights[i] : movingLights[i - n] != null ? movingLights[i - n].position : Vector3.zero;
                var start = new Vector3(p.x, seaLevel, p.z);
                var toEye = new Vector3(eye.x - p.x, 0f, eye.z - p.z);
                float dist = toEye.magnitude;
                if (dist < 1f) toEye = Vector3.forward;
                var dir = toEye / Mathf.Max(dist, 1e-3f);
                var side = new Vector3(dir.z, 0f, -dir.x) * (width * (0.6f + dist / 600f) * 0.5f);
                var end = start + dir * Mathf.Min(length * (0.5f + dist / 400f), dist * 0.8f);
                int v = i * 4;
                _v[v] = start - side;
                _v[v + 1] = start + side;
                _v[v + 2] = end + side * 1.8f;
                _v[v + 3] = end - side * 1.8f;
            }
            _mesh.vertices = _v;
        }
    }
}
