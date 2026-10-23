using UnityEngine;

namespace Cats
{
    /// <summary>A sagging cable (the garland across the street) the cat can balance on.
    /// The curve is a parabola between A and B with `sag` metres of drop in the middle.</summary>
    public class RopePath : MonoBehaviour
    {
        public Vector3 a;
        public Vector3 b;
        public float sag = 0.5f;
        [Tooltip("How close (m) to an end the cat must be to step onto the rope.")]
        public float enterRadius = 0.6f;
        public string hint = "Гирлянда: просто веди стик вперёд — кот держится сам";

        public float Length => Vector3.Distance(a, b) * 1.03f;

        public Vector3 Evaluate(float t)
        {
            var p = Vector3.Lerp(a, b, t);
            p.y -= sag * 4f * t * (1f - t);
            return p;
        }

        public Vector3 Tangent(float t)
        {
            var d = b - a;
            d.y -= sag * 4f * (1f - 2f * t);
            return d.normalized;
        }

        /// <summary>Returns 0 or 1 if `pos` stands at an end of the rope and looks along it, otherwise -1.</summary>
        public float TryEnter(Vector3 pos, Vector3 moveDir)
        {
            if (moveDir.sqrMagnitude < 0.04f) return -1f;
            var flat = new Vector3(b.x - a.x, 0f, b.z - a.z).normalized;
            if (Flat(pos - a).magnitude < enterRadius && Mathf.Abs(pos.y - a.y) < 0.6f && Vector3.Dot(moveDir.normalized, flat) > 0.5f)
                return 0f;
            if (Flat(pos - b).magnitude < enterRadius && Mathf.Abs(pos.y - b.y) < 0.6f && Vector3.Dot(moveDir.normalized, -flat) > 0.5f)
                return 1f;
            return -1f;
        }

        static Vector3 Flat(Vector3 v) => new Vector3(v.x, 0f, v.z);

        void OnDrawGizmos()
        {
            Gizmos.color = Color.yellow;
            var prev = Evaluate(0f);
            for (int i = 1; i <= 16; i++)
            {
                var p = Evaluate(i / 16f);
                Gizmos.DrawLine(prev, p);
                prev = p;
            }
        }
    }
}
