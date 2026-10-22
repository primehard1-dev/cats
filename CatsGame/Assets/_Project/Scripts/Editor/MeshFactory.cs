using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Cats.EditorTools
{
    /// <summary>
    /// Procedural meshes for the level (boxes with world-space metre UVs, gable roofs, the background arc...).
    /// All meshes of one build are stored as sub-assets of a single .asset file.
    /// </summary>
    public class MeshFactory
    {
        readonly List<Vector3> _v = new List<Vector3>();
        readonly List<Vector3> _n = new List<Vector3>();
        readonly List<Vector2> _uv = new List<Vector2>();
        readonly List<int> _t = new List<int>();

        // ------------------------------------------------------------------ building blocks
        public void Clear() { _v.Clear(); _n.Clear(); _uv.Clear(); _t.Clear(); }

        /// <summary>Quad a-b-c-d (any winding); it is flipped so it faces `normal`.</summary>
        public void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal, Vector2 ua, Vector2 ub, Vector2 uc, Vector2 ud)
        {
            int i = _v.Count;
            _v.Add(a); _v.Add(b); _v.Add(c); _v.Add(d);
            for (int k = 0; k < 4; k++) _n.Add(normal);
            _uv.Add(ua); _uv.Add(ub); _uv.Add(uc); _uv.Add(ud);
            bool flip = Vector3.Dot(Vector3.Cross(b - a, c - a), normal) < 0f;
            if (!flip) { _t.Add(i); _t.Add(i + 1); _t.Add(i + 2); _t.Add(i); _t.Add(i + 2); _t.Add(i + 3); }
            else { _t.Add(i); _t.Add(i + 2); _t.Add(i + 1); _t.Add(i); _t.Add(i + 3); _t.Add(i + 2); }
        }

        public void Tri(Vector3 a, Vector3 b, Vector3 c, Vector3 normal, Vector2 ua, Vector2 ub, Vector2 uc)
        {
            int i = _v.Count;
            _v.Add(a); _v.Add(b); _v.Add(c);
            for (int k = 0; k < 3; k++) _n.Add(normal);
            _uv.Add(ua); _uv.Add(ub); _uv.Add(uc);
            bool flip = Vector3.Dot(Vector3.Cross(b - a, c - a), normal) < 0f;
            if (!flip) { _t.Add(i); _t.Add(i + 1); _t.Add(i + 2); }
            else { _t.Add(i); _t.Add(i + 2); _t.Add(i + 1); }
        }

        /// <summary>Box centred at `center` (local), UVs = world position in metres (seamless between blocks).</summary>
        public void Box(Vector3 center, Vector3 size, Matrix4x4 toWorld, float uvShift = 0f, bool skipBottom = false)
        {
            var h = size * 0.5f;
            var dirs = new[] { Vector3.right, Vector3.left, Vector3.up, Vector3.down, Vector3.forward, Vector3.back };
            foreach (var n in dirs)
            {
                if (skipBottom && n == Vector3.down) continue;
                var up = Mathf.Abs(n.y) > 0.5f ? Vector3.forward : Vector3.up;
                var right = Vector3.Cross(n, up);
                var c = center + Vector3.Scale(n, h);
                float ru = Mathf.Abs(right.x) * h.x + Mathf.Abs(right.y) * h.y + Mathf.Abs(right.z) * h.z;
                float rv = Mathf.Abs(up.x) * h.x + Mathf.Abs(up.y) * h.y + Mathf.Abs(up.z) * h.z;
                var p0 = c - right * ru - up * rv;
                var p1 = c - right * ru + up * rv;
                var p2 = c + right * ru + up * rv;
                var p3 = c + right * ru - up * rv;
                var wn = toWorld.MultiplyVector(n).normalized;
                Quad(p0, p1, p2, p3, n,
                     WorldUV(toWorld.MultiplyPoint3x4(p0), wn, uvShift), WorldUV(toWorld.MultiplyPoint3x4(p1), wn, uvShift),
                     WorldUV(toWorld.MultiplyPoint3x4(p2), wn, uvShift), WorldUV(toWorld.MultiplyPoint3x4(p3), wn, uvShift));
            }
        }

        static Vector2 WorldUV(Vector3 p, Vector3 n, float shift)
        {
            var a = new Vector3(Mathf.Abs(n.x), Mathf.Abs(n.y), Mathf.Abs(n.z));
            if (a.y >= a.x && a.y >= a.z) return new Vector2(p.x + shift, p.z);
            if (a.x >= a.z) return new Vector2(-p.z * Mathf.Sign(n.x) + shift, p.y);
            return new Vector2(p.x * Mathf.Sign(n.z) + shift, p.y);
        }

        /// <summary>Gable roof; ridge along local Z. `baseCenter` = centre of the eave rectangle.</summary>
        public void GableRoof(Vector3 baseCenter, Vector3 size)
        {
            float hx = size.x * 0.5f, hz = size.z * 0.5f, h = size.y;
            var c = baseCenter;
            var a = c + new Vector3(-hx, 0, -hz);
            var b = c + new Vector3(hx, 0, -hz);
            var cc = c + new Vector3(hx, 0, hz);
            var d = c + new Vector3(-hx, 0, hz);
            var r0 = c + new Vector3(0, h, -hz);
            var r1 = c + new Vector3(0, h, hz);
            float slope = Mathf.Sqrt(hx * hx + h * h);
            var nr = new Vector3(h, hx, 0).normalized;
            var nl = new Vector3(-h, hx, 0).normalized;
            // u along the ridge, v down the slope (tile columns run downhill)
            Quad(b, cc, r1, r0, nr, new Vector2(0, 0), new Vector2(size.z, 0), new Vector2(size.z, slope), new Vector2(0, slope));
            Quad(d, a, r0, r1, nl, new Vector2(size.z, 0), new Vector2(0, 0), new Vector2(0, slope), new Vector2(size.z, slope));
            Tri(a, b, r0, Vector3.back, new Vector2(0, 0), new Vector2(size.x, 0), new Vector2(hx, h));
            Tri(cc, d, r1, Vector3.forward, new Vector2(0, 0), new Vector2(size.x, 0), new Vector2(hx, h));
        }

        /// <summary>Inward-facing cylinder arc around `center` (background matte painting).</summary>
        public void Arc(Vector3 center, float radius, float y0, float height, float degFrom, float degTo, int segments)
        {
            for (int i = 0; i < segments; i++)
            {
                float t0 = (float)i / segments, t1 = (float)(i + 1) / segments;
                float a0 = Mathf.Lerp(degFrom, degTo, t0) * Mathf.Deg2Rad, a1 = Mathf.Lerp(degFrom, degTo, t1) * Mathf.Deg2Rad;
                var p0 = center + new Vector3(Mathf.Sin(a0) * radius, y0, Mathf.Cos(a0) * radius);
                var p1 = center + new Vector3(Mathf.Sin(a1) * radius, y0, Mathf.Cos(a1) * radius);
                var p2 = p1 + Vector3.up * height;
                var p3 = p0 + Vector3.up * height;
                var mid = (p0 + p1) * 0.5f;
                var n = (new Vector3(center.x, mid.y, center.z) - mid).normalized;
                Quad(p0, p3, p2, p1, n, new Vector2(t0, 0), new Vector2(t0, 1), new Vector2(t1, 1), new Vector2(t1, 0));
            }
        }

        public void FlatQuad(Vector3 center, Vector2 size, Vector3 normal, Vector2 uvScale)
        {
            var up = Mathf.Abs(normal.y) > 0.5f ? Vector3.forward : Vector3.up;
            var right = Vector3.Cross(normal, up);
            var hx = right * size.x * 0.5f;
            var hy = up * size.y * 0.5f;
            Quad(center - hx - hy, center - hx + hy, center + hx + hy, center + hx - hy, normal,
                 new Vector2(0, 0), new Vector2(0, uvScale.y), new Vector2(uvScale.x, uvScale.y), new Vector2(uvScale.x, 0));
        }

        /// <summary>Open cone, apex at the origin pointing up, opening downwards (fake light shaft). V = 1 at the top.</summary>
        public void Cone(float height, float radius, float topRadius = 0.05f, int segments = 14)
        {
            for (int i = 0; i < segments; i++)
            {
                float a0 = i * Mathf.PI * 2f / segments, a1 = (i + 1) * Mathf.PI * 2f / segments;
                var t0 = new Vector3(Mathf.Cos(a0) * topRadius, 0f, Mathf.Sin(a0) * topRadius);
                var t1 = new Vector3(Mathf.Cos(a1) * topRadius, 0f, Mathf.Sin(a1) * topRadius);
                var b0 = new Vector3(Mathf.Cos(a0) * radius, -height, Mathf.Sin(a0) * radius);
                var b1 = new Vector3(Mathf.Cos(a1) * radius, -height, Mathf.Sin(a1) * radius);
                var n = new Vector3(Mathf.Cos((a0 + a1) * 0.5f), 0.2f, Mathf.Sin((a0 + a1) * 0.5f)).normalized;
                float u0 = (float)i / segments, u1 = (float)(i + 1) / segments;
                Quad(b0, t0, t1, b1, n, new Vector2(u0, 0), new Vector2(u0, 1), new Vector2(u1, 1), new Vector2(u1, 0));
            }
        }

        /// <summary>Thin tube along a polyline (garland wire).</summary>
        public void Tube(IList<Vector3> path, float radius, int sides = 5)
        {
            for (int i = 0; i < path.Count - 1; i++)
            {
                var a = path[i];
                var b = path[i + 1];
                var dir = (b - a).normalized;
                var side = Vector3.Cross(dir, Vector3.up).normalized;
                if (side.sqrMagnitude < 0.5f) side = Vector3.right;
                var up = Vector3.Cross(side, dir);
                for (int k = 0; k < sides; k++)
                {
                    float ang0 = k * Mathf.PI * 2f / sides, ang1 = (k + 1) * Mathf.PI * 2f / sides;
                    var o0 = (side * Mathf.Cos(ang0) + up * Mathf.Sin(ang0)) * radius;
                    var o1 = (side * Mathf.Cos(ang1) + up * Mathf.Sin(ang1)) * radius;
                    var n = (o0 + o1).normalized;
                    Quad(a + o0, b + o0, b + o1, a + o1, n, Vector2.zero, Vector2.up, Vector2.one, Vector2.right);
                }
            }
        }

        public Mesh ToMesh(string name, bool lightmapUVs)
        {
            var m = new Mesh { name = name };
            if (_v.Count > 65000) m.indexFormat = IndexFormat.UInt32;
            m.SetVertices(_v);
            m.SetNormals(_n);
            m.SetUVs(0, _uv);
            m.SetTriangles(_t, 0);
            m.RecalculateBounds();
            m.RecalculateTangents();
            if (lightmapUVs)
            {
                var p = new UnwrapParam();
                UnwrapParam.SetDefaults(out p);
                p.packMargin = 0.02f;
                Unwrapping.GenerateSecondaryUVSet(m, p);
            }
            Clear();
            return m;
        }

        // ------------------------------------------------------------------ asset bundle of meshes
        public class Bundle
        {
            readonly string _path;
            Mesh _root;

            public Bundle(string path)
            {
                _path = path;
                AssetDatabase.DeleteAsset(path);
            }

            public Mesh Add(Mesh m)
            {
                if (_root == null)
                {
                    _root = m;
                    AssetDatabase.CreateAsset(m, _path);
                }
                else AssetDatabase.AddObjectToAsset(m, _root);
                return m;
            }

            public void Save() => AssetDatabase.SaveAssets();
        }
    }
}
