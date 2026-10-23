using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Cats
{
    /// <summary>Input of the player holding this phone: touch controls, plus keyboard / gamepad for testing in the editor.</summary>
    public class LocalCatInput : CatInputSource
    {
        public VirtualJoystick joystick;
        public JumpButton jumpButton;
        public JumpButton meowButton;
        public LookArea lookArea;
        public CatCameraRig cameraRig;
        public float stickLookSpeed = 600f;
        [Tooltip("Stick values below this are ignored")]
        public float deadZone = 0.18f;
        [Tooltip(">1 gives finer control near the centre of the stick")]
        public float responseCurve = 1.6f;
        [Tooltip("How fast (deg/s) the 'forward' of the stick follows a turning camera while the stick is held")]
        public float basisFollow = 25f;

        float _basisYaw;
        bool _basisInit;

        void Update()
        {
            if (cameraRig == null) return;
            var look = lookArea != null ? lookArea.ConsumeDelta() : Vector2.zero;
            look += DeviceLook() * Time.deltaTime;
            cameraRig.AddLook(look);
        }

        public override CatInputFrame Read()
        {
            var stick = joystick != null ? joystick.Value : Vector2.zero;
            var dev = DeviceMove();
            if (dev.sqrMagnitude > stick.sqrMagnitude) stick = dev;
            stick = Shape(Vector2.ClampMagnitude(stick, 1f));

            var frame = new CatInputFrame { moveRaw = stick };
            var cam = cameraRig != null ? cameraRig.transform : null;
            if (cam != null)
            {
                // the stick's "forward" is locked while the finger is down, so a camera turn never bends the path
                float camYaw = cam.eulerAngles.y;
                if (!_basisInit || stick.sqrMagnitude < 0.0001f) _basisYaw = camYaw;
                else _basisYaw = Mathf.MoveTowardsAngle(_basisYaw, camYaw, basisFollow * Time.deltaTime);
                _basisInit = true;
                var basis = Quaternion.Euler(0f, _basisYaw, 0f);
                frame.moveWorld = basis * new Vector3(stick.x, 0f, stick.y);
            }
            else
            {
                frame.moveWorld = new Vector3(stick.x, 0f, stick.y);
            }
            bool buttonPress = jumpButton != null && jumpButton.ConsumePress();
            frame.jumpDown = buttonPress || DeviceJumpDown();
            frame.jumpHeld = (jumpButton != null && jumpButton.Held) || DeviceJumpHeld();
            frame.meowDown = (meowButton != null && meowButton.ConsumePress()) || DeviceMeowDown();
            return frame;
        }

        /// <summary>Dead zone + response curve: small thumb movements give a slow, precise walk.</summary>
        Vector2 Shape(Vector2 v)
        {
            float m = v.magnitude;
            if (m <= deadZone) return Vector2.zero;
            float k = Mathf.Pow((m - deadZone) / (1f - deadZone), responseCurve);
            return v / m * k;
        }

#if ENABLE_INPUT_SYSTEM
        static Vector2 DeviceMove()
        {
            var v = Vector2.zero;
            var kb = Keyboard.current;
            if (kb != null)
            {
                if (kb.wKey.isPressed || kb.upArrowKey.isPressed) v.y += 1f;
                if (kb.sKey.isPressed || kb.downArrowKey.isPressed) v.y -= 1f;
                if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) v.x += 1f;
                if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) v.x -= 1f;
                if (v != Vector2.zero) v = v.normalized * (kb.leftShiftKey.isPressed ? 1f : 0.5f);
            }
            var gp = Gamepad.current;
            if (gp != null)
            {
                var s = gp.leftStick.ReadValue();
                if (s.sqrMagnitude > v.sqrMagnitude) v = s;
            }
            return v;
        }

        Vector2 DeviceLook()
        {
            var v = Vector2.zero;
            var gp = Gamepad.current;
            if (gp != null) v += gp.rightStick.ReadValue() * stickLookSpeed;
            var mouse = Mouse.current;
            if (mouse != null && mouse.rightButton.isPressed) v += mouse.delta.ReadValue() / Mathf.Max(Time.deltaTime, 1e-3f);
            return v;
        }

        static bool DeviceJumpDown()
        {
            var kb = Keyboard.current;
            var gp = Gamepad.current;
            return (kb != null && kb.spaceKey.wasPressedThisFrame) || (gp != null && gp.buttonSouth.wasPressedThisFrame);
        }

        static bool DeviceJumpHeld()
        {
            var kb = Keyboard.current;
            var gp = Gamepad.current;
            return (kb != null && kb.spaceKey.isPressed) || (gp != null && gp.buttonSouth.isPressed);
        }

        static bool DeviceMeowDown()
        {
            var kb = Keyboard.current;
            var gp = Gamepad.current;
            return (kb != null && kb.mKey.wasPressedThisFrame) || (gp != null && gp.buttonNorth.wasPressedThisFrame);
        }
#else
        static Vector2 DeviceMove()
        {
            var v = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
            if (v != Vector2.zero) v = v.normalized * (Input.GetKey(KeyCode.LeftShift) ? 1f : 0.5f);
            return v;
        }

        Vector2 DeviceLook()
        {
            if (!Input.GetMouseButton(1)) return Vector2.zero;
            return new Vector2(Input.GetAxis("Mouse X"), Input.GetAxis("Mouse Y")) * 20f / Mathf.Max(Time.deltaTime, 1e-3f);
        }

        static bool DeviceJumpDown() => Input.GetKeyDown(KeyCode.Space);
        static bool DeviceJumpHeld() => Input.GetKey(KeyCode.Space);
        static bool DeviceMeowDown() => Input.GetKeyDown(KeyCode.M);
#endif
    }
}
