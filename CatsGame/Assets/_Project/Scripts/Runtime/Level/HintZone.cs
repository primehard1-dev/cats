using UnityEngine;

namespace Cats
{
    [RequireComponent(typeof(BoxCollider))]
    public class HintZone : MonoBehaviour
    {
        [TextArea] public string text;
        public float seconds = 4f;

        void OnTriggerEnter(Collider other)
        {
            if (other.GetComponent<CatController>() != null && GameManager.Instance != null)
                GameManager.Instance.ShowHintOnce(text, seconds);
        }
    }
}
