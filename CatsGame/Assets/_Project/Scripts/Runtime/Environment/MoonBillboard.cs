using UnityEngine;

namespace Cats
{
    /// <summary>Keeps the HDR moon disc at a fixed direction from the camera (no parallax), facing it.</summary>
    public class MoonBillboard : MonoBehaviour
    {
        public Vector3 direction = new Vector3(0.4f, 0.19f, 0.9f);
        public float distance = 250f;

        void LateUpdate()
        {
            var cam = Camera.main;
            if (cam == null) return;
            var d = direction.normalized;
            transform.position = cam.transform.position + d * distance;
            transform.rotation = Quaternion.LookRotation(d, Vector3.up);
        }
    }
}
