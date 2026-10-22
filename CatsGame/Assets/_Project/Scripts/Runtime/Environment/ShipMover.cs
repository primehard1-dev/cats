using UnityEngine;

namespace Cats
{
    /// <summary>The cruise ship slowly crosses the bay and loops.</summary>
    public class ShipMover : MonoBehaviour
    {
        public float speed = 1.2f;
        public float travel = 900f;
        Vector3 _start;

        void Start() => _start = transform.position;

        void Update()
        {
            float s = Mathf.Repeat(Time.time * speed, travel) - travel * 0.5f;
            transform.position = _start + transform.right * -s;
        }
    }
}
