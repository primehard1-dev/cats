using UnityEngine;

namespace Cats
{
    /// <summary>
    /// Cat movement: walk/run, free jump, precise jumps onto paw markers, narrow ledges,
    /// sliding awnings, balancing on a rope, grabbing edges with the claws.
    /// The controller only consumes <see cref="CatInputFrame"/>, so a remote player can drive it too.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class CatController : MonoBehaviour
    {
        public enum State { Normal, MarkerJump, Rope, Hang, Climb, Frozen }

        [Header("Wiring")]
        public CatInputSource input;
        public CatCameraRig cameraRig;
        public int playerIndex;
        public LayerMask environmentMask = ~0;

        [Header("Movement")]
        public float walkSpeed = 1.2f;
        public float runSpeed = 3.5f;
        public float ledgeSpeed = 0.8f;
        public float acceleration = 12f;
        public float airControl = 0.35f;
        public float turnSpeed = 720f;

        [Header("Jump")]
        public float jumpHeight = 1.0f;
        public float jumpForward = 2.0f;
        public float gravity = 18f;
        public float coyoteTime = 0.12f;
        public float jumpBuffer = 0.15f;
        public float safeFall = 4.2f;

        [Header("Paw markers")]
        public float markerRange = 3.2f;
        public float markerUp = 1.8f;
        public float markerDown = 4.5f;
        public float markerCone = 60f;

        [Header("Slide / rope / claws")]
        public float slideAccel = 2.5f;
        public float slideMax = 1.4f;
        public float ropeSpeed = 0.9f;
        public float ropeDrift = 0.8f;
        public float ropeCorrection = 2.4f;
        public float grabReach = 0.32f;

        public State CurrentState { get; private set; }
        public CatCameraRig CameraRig => cameraRig;
        public bool IsGrounded { get; private set; }
        public Vector3 Velocity => _velocity;
        public float Speed01 => new Vector3(_velocity.x, 0f, _velocity.z).magnitude / runSpeed;
        public float Balance { get; private set; }
        public bool OnLedge => _ledge != null;
        public event System.Action Landed;
        public event System.Action Jumped;

        CharacterController _cc;
        Vector3 _velocity;
        float _lastGroundedTime = -10f;
        float _jumpBufferTimer;
        float _airApex;
        bool _wasGrounded;
        Collider _groundCollider;
        Vector3 _groundNormal = Vector3.up;
        LedgeZone _ledge;
        float _grabCooldown;

        // marker jump
        Vector3 _jumpStart, _jumpV0;
        float _jumpTime, _jumpDuration;

        // rope
        RopePath _rope;
        float _ropeT, _ropeSeed;

        // hang / climb
        Vector3 _hangPoint, _climbFrom;
        float _stateTime;

        static RopePath[] _ropes;

        void Awake()
        {
            _cc = GetComponent<CharacterController>();
            _airApex = transform.position.y;
        }

        void Start()
        {
            _ropes = FindRopes();
        }

        static RopePath[] FindRopes()
        {
#if UNITY_2023_1_OR_NEWER
            return Object.FindObjectsByType<RopePath>(FindObjectsSortMode.None);
#else
            return Object.FindObjectsOfType<RopePath>();
#endif
        }

        void Update()
        {
            float dt = Time.deltaTime;
            var frame = input != null && CurrentState != State.Frozen ? input.Read() : default;
            if (frame.jumpDown) _jumpBufferTimer = jumpBuffer;
            else _jumpBufferTimer -= dt;
            _grabCooldown -= dt;
            _stateTime += dt;

            switch (CurrentState)
            {
                case State.Normal: UpdateNormal(frame, dt); break;
                case State.MarkerJump: UpdateMarkerJump(dt); break;
                case State.Rope: UpdateRope(frame, dt); break;
                case State.Hang: UpdateHang(frame); break;
                case State.Climb: UpdateClimb(); break;
                case State.Frozen: break;
            }
        }

        // ------------------------------------------------------------------ normal
        void UpdateNormal(CatInputFrame frame, float dt)
        {
            var pos = transform.position;
            IsGrounded = _cc.isGrounded;
            if (IsGrounded)
            {
                _lastGroundedTime = Time.time;
                if (!_wasGrounded) OnLand();
            }
            else
            {
                if (_wasGrounded) _airApex = pos.y;
                _airApex = Mathf.Max(_airApex, pos.y);
                _groundCollider = null;
            }
            _wasGrounded = IsGrounded;

            float mag = Mathf.Clamp01(frame.moveWorld.magnitude);
            float speed = mag < 0.5f ? walkSpeed * (mag / 0.5f) : Mathf.Lerp(walkSpeed, runSpeed, (mag - 0.5f) / 0.5f);
            if (_ledge != null) speed = Mathf.Min(speed, ledgeSpeed);
            var desired = mag > 0.05f ? frame.moveWorld.normalized * speed : Vector3.zero;

            var hv = new Vector3(_velocity.x, 0f, _velocity.z);
            hv = Vector3.MoveTowards(hv, desired, acceleration * (IsGrounded ? 1f : airControl) * dt);
            var correction = Vector3.zero;

            if (IsGrounded)
            {
                if (_ledge != null) correction = _ledge.CenterPull(pos) * Mathf.Min(1f, 4f * dt);
                var kind = GroundKind();
                if (kind == SurfaceKind.Slide)
                {
                    var slope = Vector3.ProjectOnPlane(Vector3.down, _groundNormal).normalized;
                    hv += new Vector3(slope.x, 0f, slope.z) * slideAccel * dt;
                    if (hv.magnitude > slideMax) hv = hv.normalized * slideMax;
                }
                else if (mag < 0.6f && hv.sqrMagnitude > 0.01f && !HasFloorAhead(pos, hv.normalized))
                {
                    // careful walk: a cat does not step off an edge unless the player runs
                    hv = Vector3.zero;
                }

                if (TryEnterRope(pos, desired)) return;
            }

            if (hv.sqrMagnitude > 0.02f)
            {
                var look = Quaternion.LookRotation(new Vector3(hv.x, 0f, hv.z));
                transform.rotation = Quaternion.RotateTowards(transform.rotation, look, turnSpeed * dt);
            }

            bool canJump = IsGrounded || Time.time - _lastGroundedTime < coyoteTime;
            if (_jumpBufferTimer > 0f && canJump)
            {
                _jumpBufferTimer = 0f;
                _lastGroundedTime = -10f;
                if (TryMarkerJump(frame, pos)) return;
                if (_ledge == null)
                {
                    _velocity.y = Mathf.Sqrt(2f * gravity * jumpHeight);
                    if (hv.magnitude < jumpForward * 0.5f && mag > 0.1f) hv = frame.moveWorld.normalized * jumpForward * 0.5f;
                    _airApex = pos.y;
                    Jumped?.Invoke();
                }
            }

            if (IsGrounded && _velocity.y < 0f) _velocity.y = -2f;
            else _velocity.y -= gravity * dt;

            if (!IsGrounded && _velocity.y < -0.5f && _grabCooldown <= 0f && TryGrab(pos)) return;

            _velocity = new Vector3(hv.x, _velocity.y, hv.z);
            _cc.Move(_velocity * dt + correction);
        }

        SurfaceKind GroundKind()
        {
            if (_groundCollider == null) return SurfaceKind.Normal;
            var tag = _groundCollider.GetComponent<SurfaceTag>();
            return tag != null ? tag.kind : SurfaceKind.Normal;
        }

        bool HasFloorAhead(Vector3 pos, Vector3 dir)
        {
            var origin = pos + dir * 0.28f + Vector3.up * 0.3f;
            return Physics.Raycast(origin, Vector3.down, 1.4f, environmentMask, QueryTriggerInteraction.Ignore);
        }

        void OnLand()
        {
            float fall = _airApex - transform.position.y;
            Landed?.Invoke();
            if (fall > safeFall && GameManager.Instance != null) GameManager.Instance.Respawn(this);
        }

        void OnControllerColliderHit(ControllerColliderHit hit)
        {
            if (hit.normal.y > 0.55f && hit.point.y < transform.position.y + 0.15f)
            {
                _groundCollider = hit.collider;
                _groundNormal = hit.normal;
            }
            var rb = hit.rigidbody;
            if (rb != null && !rb.isKinematic && hit.moveDirection.y > -0.3f)
                rb.AddForceAtPosition(hit.moveDirection * 1.2f, hit.point, ForceMode.Impulse);
        }

        void OnTriggerEnter(Collider other)
        {
            var ledge = other.GetComponent<LedgeZone>();
            if (ledge != null) _ledge = ledge;
        }

        void OnTriggerExit(Collider other)
        {
            if (_ledge != null && other.GetComponent<LedgeZone>() == _ledge) _ledge = null;
        }

        // ------------------------------------------------------------------ paw marker jump
        bool TryMarkerJump(CatInputFrame frame, Vector3 pos)
        {
            var dir = frame.moveWorld.sqrMagnitude > 0.04f ? frame.moveWorld.normalized : transform.forward;
            JumpMarker best = null;
            float bestScore = float.MaxValue;
            foreach (var m in JumpMarker.All)
            {
                var d = m.LandingPoint - pos;
                var flat = new Vector3(d.x, 0f, d.z);
                float hd = flat.magnitude;
                if (hd < 0.35f || hd > markerRange || d.y > markerUp || d.y < -markerDown) continue;
                float angle = Vector3.Angle(flat, dir);
                if (angle > markerCone * 0.5f) continue;
                if (Physics.Linecast(pos + Vector3.up * 0.5f, m.LandingPoint + Vector3.up * 0.5f, environmentMask,
                        QueryTriggerInteraction.Ignore)) continue;
                float score = hd + angle * 0.03f;
                if (score < bestScore) { bestScore = score; best = m; }
            }
            if (best == null) return false;

            var target = best.LandingPoint + Vector3.up * 0.02f;
            var delta = target - pos;
            float h = new Vector3(delta.x, 0f, delta.z).magnitude;
            _jumpDuration = Mathf.Clamp(0.3f + h * 0.09f + Mathf.Max(0f, delta.y) * 0.12f, 0.32f, 0.75f);
            _jumpStart = pos;
            _jumpV0 = delta / _jumpDuration + Vector3.up * (0.5f * gravity * _jumpDuration);
            _jumpTime = 0f;
            transform.rotation = Quaternion.LookRotation(new Vector3(delta.x, 0f, delta.z));
            SetState(State.MarkerJump);
            Jumped?.Invoke();
            return true;
        }

        void UpdateMarkerJump(float dt)
        {
            _jumpTime = Mathf.Min(_jumpTime + dt, _jumpDuration);
            var t = _jumpTime;
            var want = _jumpStart + _jumpV0 * t + Vector3.down * (0.5f * gravity * t * t);
            var before = transform.position;
            _cc.Move(want - before);
            bool blocked = (transform.position - want).sqrMagnitude > 0.04f;
            if (blocked || _jumpTime >= _jumpDuration)
            {
                _velocity = blocked ? (_jumpV0 + Vector3.down * gravity * t) * 0.3f : Vector3.down;
                _airApex = transform.position.y;
                _wasGrounded = false;
                SetState(State.Normal);
            }
            IsGrounded = false;
        }

        // ------------------------------------------------------------------ rope
        bool TryEnterRope(Vector3 pos, Vector3 desired)
        {
            if (_ropes == null) return false;
            foreach (var rope in _ropes)
            {
                float t = rope.TryEnter(pos, desired);
                if (t < 0f) continue;
                _rope = rope;
                _ropeT = t;
                _ropeSeed = Random.value * 100f;
                Balance = 0f;
                _cc.enabled = false;
                SetState(State.Rope);
                if (GameManager.Instance != null) GameManager.Instance.ShowHintOnce(rope.hint, 4f);
                return true;
            }
            return false;
        }

        void UpdateRope(CatInputFrame frame, float dt)
        {
            var tan = _rope.Tangent(_ropeT);
            var flat = new Vector3(tan.x, 0f, tan.z).normalized;
            var right = Vector3.Cross(Vector3.up, transform.forward);
            float along = Vector3.Dot(frame.moveWorld, flat);
            float lateral = Vector3.Dot(frame.moveWorld, right);

            _ropeT += along * ropeSpeed / _rope.Length * dt;
            if (Mathf.Abs(along) > 0.1f)
                transform.rotation = Quaternion.RotateTowards(transform.rotation, Quaternion.LookRotation(flat * Mathf.Sign(along)), turnSpeed * dt);

            float noise = (Mathf.PerlinNoise(Time.time * 0.7f, _ropeSeed) - 0.5f) * 2f;
            float drift = noise * ropeDrift * (0.4f + Mathf.Abs(along)) + Balance * 0.8f;
            Balance = Mathf.Clamp(Balance + (drift + lateral * ropeCorrection) * dt, -1.2f, 1.2f);

            if (Mathf.Abs(Balance) >= 1f)
            {
                var side = right * Mathf.Sign(Balance);
                transform.position += side * 0.25f;
                ExitRope(side * 1.5f + Vector3.down);
                return;
            }
            if (_ropeT >= 1f || _ropeT <= 0f)
            {
                float t = Mathf.Clamp01(_ropeT);
                var end = _rope.Evaluate(t) + flat * (t >= 1f ? 0.35f : -0.35f) + Vector3.up * 0.05f;
                transform.position = end;
                ExitRope(Vector3.zero);
                return;
            }
            transform.position = _rope.Evaluate(_ropeT);
            _velocity = flat * along * ropeSpeed;
        }

        void ExitRope(Vector3 velocity)
        {
            _rope = null;
            Balance = 0f;
            _cc.enabled = true;
            _velocity = velocity;
            _airApex = transform.position.y;
            _wasGrounded = false;
            SetState(State.Normal);
        }

        // ------------------------------------------------------------------ claws
        bool TryGrab(Vector3 pos)
        {
            var fwd = transform.forward;
            var origin = pos + Vector3.up * 0.55f + fwd * grabReach;
            if (!Physics.Raycast(origin, Vector3.down, out var hit, 0.6f, environmentMask, QueryTriggerInteraction.Ignore)) return false;
            if (hit.normal.y < 0.7f) return false;
            float ledgeY = hit.point.y;
            if (ledgeY < pos.y + 0.05f || ledgeY > pos.y + 0.5f) return false;
            if (Physics.CheckSphere(hit.point + Vector3.up * 0.2f, 0.1f, environmentMask, QueryTriggerInteraction.Ignore)) return false;
            _hangPoint = hit.point;
            _velocity = Vector3.zero;
            var hang = new Vector3(pos.x, ledgeY - 0.33f, pos.z);
            _cc.enabled = false;
            transform.position = hang;
            _cc.enabled = true;
            SetState(State.Hang);
            return true;
        }

        void UpdateHang(CatInputFrame frame)
        {
            if (_stateTime < 0.15f) return;
            if (frame.moveRaw.y > 0.5f || frame.jumpDown)
            {
                _climbFrom = transform.position;
                _cc.enabled = false;
                SetState(State.Climb);
            }
            else if (frame.moveRaw.y < -0.5f)
            {
                _grabCooldown = 0.4f;
                _velocity = Vector3.down;
                SetState(State.Normal);
            }
        }

        void UpdateClimb()
        {
            const float duration = 0.35f;
            float t = Mathf.Clamp01(_stateTime / duration);
            var to = _hangPoint + transform.forward * 0.2f + Vector3.up * 0.02f;
            var p = Vector3.Lerp(_climbFrom, to, t);
            p.y += Mathf.Sin(t * Mathf.PI) * 0.12f;
            transform.position = p;
            if (t >= 1f)
            {
                _cc.enabled = true;
                _velocity = Vector3.zero;
                _airApex = transform.position.y;
                SetState(State.Normal);
            }
        }

        // ------------------------------------------------------------------ external API
        void SetState(State s)
        {
            CurrentState = s;
            _stateTime = 0f;
        }

        public void Teleport(Vector3 position, float yaw)
        {
            _cc.enabled = false;
            transform.SetPositionAndRotation(position, Quaternion.Euler(0f, yaw, 0f));
            _cc.enabled = true;
            _velocity = Vector3.zero;
            _airApex = position.y;
            _wasGrounded = false;
            _rope = null;
            _ledge = null;
            Balance = 0f;
            SetState(State.Normal);
        }

        public void SetFrozen(bool frozen)
        {
            if (frozen) { _velocity = Vector3.zero; SetState(State.Frozen); }
            else if (CurrentState == State.Frozen) SetState(State.Normal);
        }
    }
}
