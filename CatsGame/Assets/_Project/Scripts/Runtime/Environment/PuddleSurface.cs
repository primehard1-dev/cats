using System.Collections.Generic;
using UnityEngine;

namespace Cats
{
    /// <summary>A flat wet floor (terrace, roof terrace, café, quay) that can show planar reflections.</summary>
    [RequireComponent(typeof(Renderer))]
    public class PuddleSurface : MonoBehaviour
    {
        public static readonly List<PuddleSurface> All = new List<PuddleSurface>();

        Renderer _renderer;
        Bounds _area;

        public float Height => transform.position.y;
        public Bounds Area => _area;

        void Awake()
        {
            _renderer = GetComponent<Renderer>();
            _area = _renderer.bounds;
        }
        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        public float DistanceTo(Vector3 p) => Mathf.Sqrt(Area.SqrDistance(p));

        public void SetVisible(bool visible)
        {
            if (_renderer != null) _renderer.enabled = visible;
        }
    }
}
