using UnityEngine;

namespace Cats
{
    [RequireComponent(typeof(BoxCollider))]
    public class KillZone : MonoBehaviour
    {
        void OnTriggerEnter(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat != null && GameManager.Instance != null) GameManager.Instance.Respawn(cat);
        }
    }
}
