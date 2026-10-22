using UnityEngine;

namespace Cats
{
    /// <summary>
    /// Procedural animation for the cat: walk/run gait, jump and hang poses, rope balance, sitting,
    /// breathing, idle glances, meow. Works on any skeleton whose bones are named
    /// Body, Head, Leg_FL/FR/BL/BR, Tail1..N — every rotation is applied around the cat's own
    /// right / up / forward axes expressed in the bone's parent space, so bone roll does not matter.
    /// </summary>
    public class CatAnimator : MonoBehaviour
    {
        public CatController controller;
        public Transform model;
        public float stepFrequency = 7.5f;
        public float legSwing = 32f;
        public float sitAfter = 4f;

        Transform _body, _head;
        readonly Transform[] _legs = new Transform[4];
        Transform[] _tail;
        Quaternion _bodyRest, _headRest;
        readonly Quaternion[] _legRest = new Quaternion[4];
        Quaternion[] _tailRest;
        Vector3 _bodyPos, _bodyScale;
        float _phase, _land, _lean, _sit, _meow, _nextGlance;
        Transform _lookTarget;
        Vector3 _glance;

        static readonly string[] LegNames = { "Leg_FL", "Leg_FR", "Leg_BL", "Leg_BR" };
        static readonly float[] LegPhase = { 0f, Mathf.PI, Mathf.PI, 0f };

        public bool IsSitting => _sit > 0.9f;
        public float SitTime { get; private set; }

        public void PlayMeow() => _meow = 1f;
        public void LookAt(Transform target) => _lookTarget = target;

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
            if (_body != null)
            {
                _bodyRest = _body.localRotation;
                _bodyPos = _body.localPosition;
                _bodyScale = _body.localScale;
            }
            if (_head != null) _headRest = _head.localRotation;
            if (controller != null) controller.Landed += () => _land = 1f;
        }

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

        /// <summary>rest pose rotated by `angle` degrees around a cat-space axis (right/up/forward of the cat).</summary>
        Quaternion Around(Transform bone, Quaternion rest, Vector3 catAxis, float angle)
        {
            var parent = bone.parent != null ? bone.parent : transform;
            var axis = parent.InverseTransformDirection(transform.TransformDirection(catAxis));
            return Quaternion.AngleAxis(angle, axis) * rest;
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
            float k20 = 1f - Mathf.Exp(-dt * 20f);

            // body: pitch (+ = nose down), lean on the rope, sit down, breathe
            float pitch = hang ? -45f : air ? (controller.Velocity.y > 0 ? -12f : 10f) : 0f;
            pitch = Mathf.Lerp(pitch, -20f, _sit);
            _lean = Mathf.Lerp(_lean, rope ? controller.Balance * 30f : 0f, 1f - Mathf.Exp(-dt * 10f));
            float bob = Mathf.Abs(Mathf.Sin(_phase)) * 0.012f * Mathf.Clamp01(speed * 2f);
            var parent = _body.parent != null ? _body.parent : transform;
            var up = parent.InverseTransformVector(transform.up).normalized;
            float unit = parent.InverseTransformVector(transform.up).magnitude;
            _body.localPosition = _bodyPos + up * unit * (bob - _land * 0.03f - 0.05f * _sit);
            float breathe = Mathf.Sin(Time.time * 2.4f) * 0.012f;
            _body.localScale = _bodyScale * (1f + breathe * 0.6f);
            var bodyRot = Around(_body, _bodyRest, Vector3.right, pitch);
            bodyRot = Quaternion.AngleAxis(_lean, parent.InverseTransformDirection(transform.forward)) * bodyRot;
            _body.localRotation = Quaternion.Slerp(_body.localRotation, bodyRot, 1f - Mathf.Exp(-dt * 12f));

            // legs: + angle swings the paw backwards
            for (int i = 0; i < 4; i++)
            {
                if (_legs[i] == null) continue;
                bool front = i < 2;
                float a;
                if (air) a = front ? -40f : 40f;
                else if (hang) a = front ? -70f : 15f;
                else a = Mathf.Sin(_phase + LegPhase[i]) * amp;
                a = Mathf.Lerp(a, front ? 20f : -15f, _sit);
                _legs[i].localRotation = Quaternion.Slerp(_legs[i].localRotation, Around(_legs[i], _legRest[i], Vector3.right, a), k20);
            }

            // head: look at the NPC, glance around when idle, lift for a meow
            if (_head != null)
            {
                float yaw = 0f, nod = Mathf.Sin(_phase * 2f) * 2f * speed;
                if (_lookTarget != null)
                {
                    var local = transform.InverseTransformPoint(_lookTarget.position);
                    yaw = Mathf.Clamp(Mathf.Atan2(local.x, local.z) * Mathf.Rad2Deg, -60f, 60f);
                }
                else if (controller.IdleTime > 1.5f)
                {
                    if (Time.time > _nextGlance)
                    {
                        _glance = new Vector3(Random.Range(-15f, 20f), Random.Range(-70f, 70f), 0f);
                        _nextGlance = Time.time + Random.Range(1.5f, 4f);
                    }
                    yaw = _glance.y;
                    nod = _glance.x * (1f - _sit * 0.5f) + 12f * _sit;
                }
                nod -= 25f * Mathf.Sin(_meow * Mathf.PI);
                var hr = Around(_head, _headRest, Vector3.right, nod);
                var hp = _head.parent != null ? _head.parent : transform;
                hr = Quaternion.AngleAxis(yaw, hp.InverseTransformDirection(transform.up)) * hr;
                _head.localRotation = Quaternion.Slerp(_head.localRotation, hr, 1f - Mathf.Exp(-dt * 6f));
            }

            // tail: raised when walking (each segment curls a bit), down when sitting, sways
            float t = Time.time;
            for (int i = 0; i < _tail.Length; i++)
            {
                float k = (i + 1f) / Mathf.Max(1, _tail.Length);
                float sway = Mathf.Sin(t * 1.6f - i * 0.6f) * (5f + 8f * k) * (rope ? 2.2f : 1f);
                if (rope) sway += -controller.Balance * 25f * k;
                sway *= Mathf.Lerp(1f, 0.4f, _sit);
                float lift = air ? -2f : 4f + 7f * speed;
                lift = Mathf.Lerp(lift, -9f, _sit);
                var tp = _tail[i].parent != null ? _tail[i].parent : transform;
                var r = Around(_tail[i], _tailRest[i], Vector3.right, lift);
                r = Quaternion.AngleAxis(sway, tp.InverseTransformDirection(transform.up)) * r;
                _tail[i].localRotation = r;
            }
        }
    }
}
