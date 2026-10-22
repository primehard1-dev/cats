using UnityEngine;
using UnityEngine.EventSystems;

namespace Cats
{
    /// <summary>Full-screen transparent area behind the buttons: drag to rotate the camera.</summary>
    public class LookArea : MonoBehaviour, IPointerDownHandler, IDragHandler, IPointerUpHandler
    {
        Vector2 _delta;
        int _pointer = int.MinValue;

        public void OnPointerDown(PointerEventData e)
        {
            if (_pointer == int.MinValue) _pointer = e.pointerId;
        }

        public void OnDrag(PointerEventData e)
        {
            if (e.pointerId == _pointer) _delta += e.delta;
        }

        public void OnPointerUp(PointerEventData e)
        {
            if (e.pointerId == _pointer) _pointer = int.MinValue;
        }

        /// <summary>Accumulated drag in pixels since the last call, normalised to a 1080p-high screen.</summary>
        public Vector2 ConsumeDelta()
        {
            var d = _delta * (1080f / Mathf.Max(1, Screen.height));
            _delta = Vector2.zero;
            return d;
        }
    }
}
