using System.Collections.Generic;
using UnityEngine;

namespace Cats
{
    /// <summary>
    /// Third-person camera that frames the cat like the reference shot: behind and above,
    /// the cat in the lower third, the street and the sea in the middle of the frame.
    /// One rig per local player (each phone renders its own view in co-op).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class CatCameraRig : MonoBehaviour
    {
        public Transform target;
        public LayerMask collisionMask = ~0;

        [Header("Framing")]
        public float distance = 3.9f;
        [Tooltip("Orbit elevation in degrees: how high above the cat the camera sits.")]
        public float orbitPitch = 30f;
        [Tooltip("Camera tilt in degrees: below orbitPitch so the view goes past the cat towards the horizon.")]
        public float viewPitch = 13f;
        public float side;
        public float pivotHeight = 0.35f;

        [Header("Control")]
        public float lookSensitivity = 0.15f;
        public float minPitch = 5f;
        public float maxPitch = 65f;
        public float recenterDelay = 1.6f;
        public float recenterSpeed = 60f;
        public float damping = 10f;
        public float collisionRadius = 0.15f;

        float _yaw, _pitch, _dist, _view, _side;
        float _lastLook = -10f;
        readonly List<CameraZone> _zones = new List<CameraZone>();
        Vector3 _pivot;

        public float Yaw => _yaw;

        void Start()
        {
            _pitch = orbitPitch;
            _dist = distance;
            _view = viewPitch;
            if (target != null)
            {
                _yaw = target.eulerAngles.y;
                _pivot = target.position + Vector3.up * pivotHeight;
                Snap();
            }
        }

        /// <summary>Look input in screen pixels (touch drag / mouse) or stick units scaled by the caller.</summary>
        public void AddLook(Vector2 delta)
        {
            if (delta.sqrMagnitude < 1e-6f) return;
            _yaw += delta.x * lookSensitivity;
            _pitch = Mathf.Clamp(_pitch - delta.y * lookSensitivity, minPitch, maxPitch);
            _lastLook = Time.time;
        }

        public void PushZone(CameraZone z) { if (!_zones.Contains(z)) _zones.Add(z); }
        public void PopZone(CameraZone z) { _zones.Remove(z); }

        public void Snap()
        {
            if (target == null) return;
            _yaw = target.eulerAngles.y;
            _pivot = target.position + Vector3.up * pivotHeight;
            Apply(1f);
        }

        void LateUpdate()
        {
            if (target == null) return;
            float dt = Time.deltaTime;
            float wantDist = distance, wantView = viewPitch, wantSide = side, wantOrbit = orbitPitch;
            if (_zones.Count > 0)
            {
                var z = _zones[_zones.Count - 1];
                wantDist = z.distance;
                wantOrbit = Mathf.Atan2(z.height, z.distance) * Mathf.Rad2Deg;
                wantView = z.pitch;
                wantSide = z.side;
            }
            float k = 1f - Mathf.Exp(-dt * 3f);
            _dist = Mathf.Lerp(_dist, wantDist, k);
            _view = Mathf.Lerp(_view, wantView, k);
            _side = Mathf.Lerp(_side, wantSide, k);
            if (Time.time - _lastLook > recenterDelay)
            {
                _pitch = Mathf.MoveTowards(_pitch, wantOrbit, 20f * dt);
                var cat = target.GetComponent<CatController>();
                if (cat != null && cat.Speed01 > 0.15f)
                    _yaw = Mathf.MoveTowardsAngle(_yaw, target.eulerAngles.y, recenterSpeed * cat.Speed01 * dt);
            }
            _pivot = Vector3.Lerp(_pivot, target.position + Vector3.up * pivotHeight, 1f - Mathf.Exp(-dt * damping));
            Apply(1f - Mathf.Exp(-dt * damping));
        }

        void Apply(float blend)
        {
            var orbit = Quaternion.Euler(_pitch, _yaw, 0f);
            var right = orbit * Vector3.right;
            var desired = _pivot - orbit * Vector3.forward * _dist + right * _side;
            var dir = desired - _pivot;
            float len = dir.magnitude;
            if (len > 0.01f && Physics.SphereCast(_pivot, collisionRadius, dir / len, out var hit, len, collisionMask,
                    QueryTriggerInteraction.Ignore))
                desired = _pivot + dir / len * Mathf.Max(0.3f, hit.distance - 0.05f);
            transform.position = Vector3.Lerp(transform.position, desired, blend);
            float tilt = _view + (_pitch - orbitPitch) * 0.6f;
            transform.rotation = Quaternion.Euler(tilt, _yaw, 0f);
        }
    }
}
