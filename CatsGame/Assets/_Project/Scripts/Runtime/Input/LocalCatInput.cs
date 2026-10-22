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
        public LookArea lookArea;
        public CatCameraRig cameraRig;
        public float stickLookSpeed = 900f;

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
            stick = Vector2.ClampMagnitude(stick, 1f);

            var frame = new CatInputFrame { moveRaw = stick };
            var cam = cameraRig != null ? cameraRig.transform : null;
            if (cam != null)
            {
                var f = Vector3.ProjectOnPlane(cam.forward, Vector3.up).normalized;
                var r = Vector3.ProjectOnPlane(cam.right, Vector3.up).normalized;
                frame.moveWorld = f * stick.y + r * stick.x;
            }
            else
            {
                frame.moveWorld = new Vector3(stick.x, 0f, stick.y);
            }
            bool buttonPress = jumpButton != null && jumpButton.ConsumePress();
            frame.jumpDown = buttonPress || DeviceJumpDown();
            frame.jumpHeld = (jumpButton != null && jumpButton.Held) || DeviceJumpHeld();
            return frame;
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
#endif
    }
}
