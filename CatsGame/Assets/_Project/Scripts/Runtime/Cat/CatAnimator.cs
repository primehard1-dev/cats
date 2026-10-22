using UnityEngine;

namespace Cats
{
    /// <summary>
    /// Procedural animation for the part-based placeholder cat (Body, Head, Leg_FL/FR/BL/BR, Tail1..N).
    /// Swap for an Animator with real clips once a rigged cat model arrives; the controller does not depend on it.
    /// </summary>
    public class CatAnimator : MonoBehaviour
    {
        public CatController controller;
        public Transform model;
        public float stepFrequency = 7.5f;
        public float legSwing = 32f;

        Transform _body, _head;
        readonly Transform[] _legs = new Transform[4];
        Transform[] _tail;
        Quaternion _bodyRest, _headRest;
        readonly Quaternion[] _legRest = new Quaternion[4];
        Quaternion[] _tailRest;
        Vector3 _bodyPos;
        float _phase, _land, _lean, _sit, _meow, _nextGlance;
        Transform _lookTarget;
        Vector3 _glance;

        public bool IsSitting => _sit > 0.9f;
        public float SitTime { get; private set; }
        public float sitAfter = 4f;

        public void PlayMeow() => _meow = 1f;

        static readonly string[] LegNames = { "Leg_FL", "Leg_FR", "Leg_BL", "Leg_BR" };
        static readonly float[] LegPhase = { 0f, Mathf.PI, Mathf.PI, 0f };

        void Start()
        {
            if (model == null) model = transform;
            _body = Find(model, "Body");
            _head = Find(model, "Head");
            for (int i = 0; i < 4; i++)
            {
                _legs[i] = Find(model, LegNames[i]);
                if (_legs[i] != null) _legRest[i] = _legs[i].localRotation;
            }
            var tail = new System.Collections.Generic.List<Transform>();
            for (int i = 1; i < 12; i++)
            {
                var t = Find(model, "Tail" + i);
                if (t == null) break;
                tail.Add(t);
            }
            _tail = tail.ToArray();
            _tailRest = new Quaternion[_tail.Length];
            for (int i = 0; i < _tail.Length; i++) _tailRest[i] = _tail[i].localRotation;
            if (_body != null) { _bodyRest = _body.localRotation; _bodyPos = _body.localPosition; }
            if (_head != null) _headRest = _head.localRotation;
            if (controller != null) controller.Landed += () => _land = 1f;
        }

        public void LookAt(Transform target) => _lookTarget = target;

        static Transform Find(Transform root, string name)
        {
            if (root.name == name) return root;
            foreach (Transform c in root)
            {
                var r = Find(c, name);
                if (r != null) return r;
            }
            return null;
        }

        void LateUpdate()
        {
            if (controller == null || _body == null) return;
            float dt = Time.deltaTime;
            var state = controller.CurrentState;
            float speed = controller.Speed01;
            bool air = !controller.IsGrounded && state == CatController.State.Normal || state == CatController.State.MarkerJump;
            bool hang = state == CatController.State.Hang || state == CatController.State.Climb;
            bool rope = state == CatController.State.Rope;

            bool sitting = controller.IdleTime > sitAfter && state == CatController.State.Normal && controller.IsGrounded;
            _sit = Mathf.MoveTowards(_sit, sitting ? 1f : 0f, dt * (sitting ? 1.5f : 5f));
            SitTime = IsSitting ? SitTime + dt : 0f;
            _meow = Mathf.MoveTowards(_meow, 0f, dt * 1.6f);

            _phase += dt * stepFrequency * Mathf.Lerp(0.6f, 1.6f, speed) * (speed > 0.02f || rope ? 1f : 0f);
            _land = Mathf.MoveTowards(_land, 0f, dt * 4f);
            float amp = legSwing * Mathf.Clamp01(speed * 2.5f);
            if (rope) amp = 12f * Mathf.Clamp01(controller.Velocity.magnitude * 3f);

            for (int i = 0; i < 4; i++)
            {
                if (_legs[i] == null) continue;
                float a;
                if (air) a = i < 2 ? -40f : 40f;
                else if (hang) a = i < 2 ? -70f : 15f;
                else a = Mathf.Sin(_phase + LegPhase[i]) * amp;
                // sitting: hind legs fold under the body, front legs straight
                a = Mathf.Lerp(a, i < 2 ? -18f : 75f, _sit);
                _legs[i].localRotation = Quaternion.Slerp(_legs[i].localRotation, _legRest[i] * Quaternion.Euler(a, 0f, 0f), 1f - Mathf.Exp(-dt * 20f));
            }

            float bob = Mathf.Abs(Mathf.Sin(_phase)) * 0.012f * Mathf.Clamp01(speed * 2f);
            _body.localPosition = _bodyPos + Vector3.up * (bob - _land * 0.03f);
            _lean = Mathf.Lerp(_lean, rope ? controller.Balance * 30f : 0f, 1f - Mathf.Exp(-dt * 10f));
            float pitch = hang ? -45f : air ? (controller.Velocity.y > 0 ? -12f : 10f) : 0f;
            pitch = Mathf.Lerp(pitch, -28f, _sit);
            float breathe = Mathf.Sin(Time.time * 2.4f) * 0.012f;
            _body.localPosition += Vector3.down * (0.06f * _sit);
            _body.localScale = new Vector3(1f + breathe * 0.5f, 1f + breathe, 1f);
            _body.localRotation = Quaternion.Slerp(_body.localRotation, _bodyRest * Quaternion.Euler(pitch, 0f, _lean), 1f - Mathf.Exp(-dt * 12f));

            if (_head != null)
            {
                var headRot = _headRest * Quaternion.Euler(Mathf.Sin(_phase * 2f) * 2f * speed, 0f, 0f);
                if (_lookTarget != null)
                {
                    var local = _body.InverseTransformPoint(_lookTarget.position);
                    float yaw = Mathf.Clamp(Mathf.Atan2(local.x, local.z) * Mathf.Rad2Deg, -60f, 60f);
                    headRot = _headRest * Quaternion.Euler(0f, yaw, 0f);
                }
                else if (controller.IdleTime > 1.5f)
                {
                    // idle: glance around at the lights, the sea, the moon
                    if (Time.time > _nextGlance)
                    {
                        _glance = new Vector3(Random.Range(-15f, 25f), Random.Range(-70f, 70f), 0f);
                        _nextGlance = Time.time + Random.Range(1.5f, 4f);
                    }
                    headRot = _headRest * Quaternion.Euler(_glance.x * (1f - _sit * 0.5f) + 20f * _sit, _glance.y, 0f);
                }
                headRot *= Quaternion.Euler(-25f * Mathf.Sin(_meow * Mathf.PI), 0f, 0f);
                _head.localRotation = Quaternion.Slerp(_head.localRotation, headRot, 1f - Mathf.Exp(-dt * 6f));
            }

            float t = Time.time;
            for (int i = 0; i < _tail.Length; i++)
            {
                float k = (i + 1f) / _tail.Length;
                float sway = Mathf.Sin(t * 1.6f - i * 0.6f) * (6f + 10f * k) * (rope ? 2.2f : 1f);
                float lift = air ? -8f : speed * -6f;
                lift = Mathf.Lerp(lift, 22f, _sit);
                sway *= Mathf.Lerp(1f, 0.4f, _sit);
                if (rope) sway += -controller.Balance * 25f * k;
                _tail[i].localRotation = _tailRest[i] * Quaternion.Euler(lift, sway, 0f);
            }
        }
    }
}
