using UnityEngine;

namespace Cats
{
    [RequireComponent(typeof(BoxCollider))]
    public class LevelExit : MonoBehaviour
    {
        void OnTriggerEnter(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat != null && GameManager.Instance != null) GameManager.Instance.CompleteLevel(cat);
        }
    }
}
