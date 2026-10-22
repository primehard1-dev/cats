using UnityEngine;
using UnityEngine.EventSystems;

namespace Cats
{
    /// <summary>Jump button with the leaping cat icon (bottom-right).</summary>
    public class JumpButton : MonoBehaviour, IPointerDownHandler, IPointerUpHandler
    {
        public bool Held { get; private set; }
        bool _pressed;
        Vector3 _scale;

        void Awake() => _scale = transform.localScale;

        public void OnPointerDown(PointerEventData e)
        {
            Held = true;
            _pressed = true;
            transform.localScale = _scale * 0.92f;
        }

        public void OnPointerUp(PointerEventData e)
        {
            Held = false;
            transform.localScale = _scale;
        }

        /// <summary>True once per press.</summary>
        public bool ConsumePress()
        {
            bool p = _pressed;
            _pressed = false;
            return p;
        }
    }
}
