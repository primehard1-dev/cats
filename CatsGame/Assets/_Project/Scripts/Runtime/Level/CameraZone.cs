using UnityEngine;

namespace Cats
{
    /// <summary>Overrides the camera framing while the cat is inside.</summary>
    [RequireComponent(typeof(BoxCollider))]
    public class CameraZone : MonoBehaviour
    {
        public float distance = 3.9f;
        public float height = 1.95f;
        public float pitch = 13f;
        public float side;
        [Tooltip("Fix the camera direction in this zone (degrees around Y)")]
        public bool fixYaw;
        public float yaw;

        void OnTriggerEnter(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat != null && cat.CameraRig != null) cat.CameraRig.PushZone(this);
        }

        void OnTriggerExit(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat != null && cat.CameraRig != null) cat.CameraRig.PopZone(this);
        }
    }
}
