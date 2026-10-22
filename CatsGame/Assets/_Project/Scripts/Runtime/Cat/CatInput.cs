using UnityEngine;

namespace Cats
{
    /// <summary>One frame of player intent. Movement is already in world space so the
    /// same struct can later come from the network (co-op over a phone hotspot).</summary>
    public struct CatInputFrame
    {
        public Vector3 moveWorld;   // horizontal, magnitude 0..1
        public Vector2 moveRaw;     // stick as the player pushes it (x = right, y = forward)
        public bool jumpDown;
        public bool jumpHeld;
    }

    /// <summary>Anything that can drive a cat: local touch/keyboard, AI, or a remote player.</summary>
    public abstract class CatInputSource : MonoBehaviour
    {
        public abstract CatInputFrame Read();
    }
}
