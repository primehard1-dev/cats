using UnityEngine;

namespace Cats
{
    [RequireComponent(typeof(BoxCollider))]
    public class Checkpoint : MonoBehaviour
    {
        public string id;
        public float spawnYaw;

        public Vector3 SpawnPosition
        {
            get
            {
                var b = GetComponent<BoxCollider>();
                var p = transform.TransformPoint(b.center);
                p.y -= b.size.y * 0.5f;
                return p + Vector3.up * 0.15f;
            }
        }

        void OnTriggerEnter(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat != null && GameManager.Instance != null) GameManager.Instance.ReachCheckpoint(cat, this);
        }
    }
}
