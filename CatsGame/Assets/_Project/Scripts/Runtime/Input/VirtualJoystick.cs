using UnityEngine;
using UnityEngine.EventSystems;

namespace Cats
{
    /// <summary>On-screen stick (bottom-left, like the reference screenshot).</summary>
    public class VirtualJoystick : MonoBehaviour, IPointerDownHandler, IDragHandler, IPointerUpHandler
    {
        public RectTransform knob;
        public float radius = 110f;

        public Vector2 Value { get; private set; }
        RectTransform _rect;

        void Awake() => _rect = (RectTransform)transform;

        public void OnPointerDown(PointerEventData e) => OnDrag(e);

        public void OnDrag(PointerEventData e)
        {
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(_rect, e.position, e.pressEventCamera, out var local)) return;
            var v = Vector2.ClampMagnitude(local, radius);
            if (knob != null) knob.anchoredPosition = v;
            Value = v / radius;
        }

        public void OnPointerUp(PointerEventData e)
        {
            Value = Vector2.zero;
            if (knob != null) knob.anchoredPosition = Vector2.zero;
        }
    }
}
