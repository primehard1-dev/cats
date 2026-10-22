using UnityEngine;

namespace Cats
{
    public enum SurfaceKind { Normal, Ledge, Slide }

    /// <summary>Tags a collider with a special walking behaviour.</summary>
    public class SurfaceTag : MonoBehaviour
    {
        public SurfaceKind kind = SurfaceKind.Normal;
    }
}
