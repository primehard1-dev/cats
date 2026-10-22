using UnityEngine;

namespace Cats
{
    /// <summary>Narrow ledge: slow walk, the cat is gently pulled to the middle line.</summary>
    [RequireComponent(typeof(BoxCollider))]
    public class LedgeZone : MonoBehaviour
    {
        public string hint = "Узкий карниз — иди аккуратно";

        /// <summary>Horizontal correction that moves `pos` towards the ledge centre line (long axis = local Z).</summary>
        public Vector3 CenterPull(Vector3 pos)
        {
            var local = transform.InverseTransformPoint(pos);
            var box = GetComponent<BoxCollider>();
            var target = new Vector3(box.center.x, local.y, local.z);
            var world = transform.TransformPoint(target);
            var d = world - pos;
            d.y = 0f;
            return d;
        }

        void OnTriggerEnter(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat != null && GameManager.Instance != null) GameManager.Instance.ShowHintOnce(hint, 3f);
        }
    }
}
