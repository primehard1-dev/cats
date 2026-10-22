// Compile-check stubs for packages that are not part of UnityEngine.dll / UnityEditor.dll.
// Only signatures used by the project; verified against the package sources (URP 17, uGUI 2, Input System 1.11).
#pragma warning disable CS0067, CS0649, CS0414
using System;
using UnityEngine;

namespace UnityEngine.EventSystems
{
    public class UIBehaviour : MonoBehaviour { }
    public class EventSystem : UIBehaviour { }
    public abstract class BaseInputModule : UIBehaviour { }
    public class StandaloneInputModule : BaseInputModule { }
    public abstract class BaseRaycaster : UIBehaviour { }
    public class BaseEventData { }
    public class PointerEventData : BaseEventData
    {
        public Vector2 position { get; set; }
        public Vector2 delta { get; set; }
        public int pointerId { get; set; }
        public Camera pressEventCamera => null;
    }
    public interface IEventSystemHandler { }
    public interface IPointerDownHandler : IEventSystemHandler { void OnPointerDown(PointerEventData eventData); }
    public interface IPointerUpHandler : IEventSystemHandler { void OnPointerUp(PointerEventData eventData); }
    public interface IDragHandler : IEventSystemHandler { void OnDrag(PointerEventData eventData); }
}

namespace UnityEngine.UI
{
    using UnityEngine.EventSystems;
    public abstract class Graphic : UIBehaviour { public virtual Color color { get; set; } public bool raycastTarget { get; set; } }
    public abstract class MaskableGraphic : Graphic { }
    public class Image : MaskableGraphic { public Sprite sprite { get; set; } }
    public class Text : MaskableGraphic
    {
        public Font font { get; set; }
        public int fontSize { get; set; }
        public TextAnchor alignment { get; set; }
        public string text { get; set; }
        public HorizontalWrapMode horizontalOverflow { get; set; }
        public VerticalWrapMode verticalOverflow { get; set; }
    }
    public class CanvasScaler : UIBehaviour
    {
        public enum ScaleMode { ConstantPixelSize, ScaleWithScreenSize, ConstantPhysicalSize }
        public enum ScreenMatchMode { MatchWidthOrHeight = 0, Expand = 1, Shrink = 2 }
        public ScaleMode uiScaleMode { get; set; }
        public Vector2 referenceResolution { get; set; }
        public ScreenMatchMode screenMatchMode { get; set; }
        public float matchWidthOrHeight { get; set; }
    }
    public class GraphicRaycaster : BaseRaycaster { }
    public class RawImage : MaskableGraphic { public Texture texture { get; set; } }
    public abstract class Selectable : UIBehaviour
    {
        public Graphic targetGraphic { get; set; }
        public ColorBlock colors { get; set; }
        public bool interactable { get; set; }
    }
    public struct ColorBlock
    {
        public Color normalColor { get; set; }
        public Color highlightedColor { get; set; }
        public Color pressedColor { get; set; }
        public Color selectedColor { get; set; }
        public Color disabledColor { get; set; }
        public float colorMultiplier { get; set; }
        public float fadeDuration { get; set; }
        public static ColorBlock defaultColorBlock => default;
    }
    public class Button : Selectable
    {
        public class ButtonClickedEvent : UnityEngine.Events.UnityEvent { }
        public ButtonClickedEvent onClick { get; set; } = new ButtonClickedEvent();
    }
    public class Slider : Selectable
    {
        public enum Direction { LeftToRight, RightToLeft, BottomToTop, TopToBottom }
        public class SliderEvent : UnityEngine.Events.UnityEvent<float> { }
        public SliderEvent onValueChanged { get; set; } = new SliderEvent();
        public float value { get; set; }
        public float minValue { get; set; }
        public float maxValue { get; set; }
        public RectTransform fillRect { get; set; }
        public RectTransform handleRect { get; set; }
        public Direction direction { get; set; }
    }
    public class AspectRatioFitter : UIBehaviour
    {
        public enum AspectMode { None, WidthControlsHeight, HeightControlsWidth, FitInParent, EnvelopeParent }
        public AspectMode aspectMode { get; set; }
        public float aspectRatio { get; set; }
    }
    public class Shadow : UIBehaviour { public Color effectColor { get; set; } public Vector2 effectDistance { get; set; } }
    public class Outline : Shadow { }
}

namespace UnityEngine.InputSystem.Controls
{
    public class ButtonControl { public bool isPressed => false; public bool wasPressedThisFrame => false; }
    public class KeyControl : ButtonControl { }
    public class Vector2Control { public Vector2 ReadValue() => default; }
    public class StickControl : Vector2Control { }
    public class DeltaControl : Vector2Control { }
}

namespace UnityEngine.InputSystem
{
    using UnityEngine.InputSystem.Controls;
    public class Keyboard
    {
        public static Keyboard current => null;
        public KeyControl escapeKey, mKey, wKey, aKey, sKey, dKey, upArrowKey, downArrowKey, leftArrowKey, rightArrowKey, leftShiftKey, spaceKey;
    }
    public class Gamepad
    {
        public static Gamepad current => null;
        public StickControl leftStick, rightStick;
        public ButtonControl buttonSouth, buttonNorth;
    }
    public class Mouse
    {
        public static Mouse current => null;
        public ButtonControl rightButton;
        public DeltaControl delta;
    }
}

namespace UnityEngine.InputSystem.UI
{
    public class InputSystemUIInputModule : UnityEngine.EventSystems.BaseInputModule { public void AssignDefaultActions() { } }
}

namespace UnityEngine.Rendering
{
    public class VolumeComponent : ScriptableObject { }
    public class VolumeParameter<T> { public T value; public void Override(T x) { value = x; } }
    public class FloatParameter : VolumeParameter<float> { }
    public class MinFloatParameter : FloatParameter { }
    public class ClampedFloatParameter : FloatParameter { }
    public class BoolParameter : VolumeParameter<bool> { }
    public class ColorParameter : VolumeParameter<Color> { }
    public class VolumeProfile : ScriptableObject { public T Add<T>(bool overrides = false) where T : VolumeComponent => null; }
    public class Volume : MonoBehaviour { public bool isGlobal; public float priority; public VolumeProfile sharedProfile; }
}

namespace UnityEngine.Rendering.Universal
{
    using UnityEngine.Rendering;
    public enum TonemappingMode { None, Neutral, ACES }
    public sealed class TonemappingModeParameter : VolumeParameter<TonemappingMode> { }
    public sealed class Tonemapping : VolumeComponent { public TonemappingModeParameter mode; }
    public sealed class Bloom : VolumeComponent { public MinFloatParameter threshold, intensity; public ClampedFloatParameter scatter; public ColorParameter tint; public BoolParameter highQualityFiltering; }
    public sealed class SplitToning : VolumeComponent { public ColorParameter shadows, highlights; public ClampedFloatParameter balance; }
    public sealed class ColorAdjustments : VolumeComponent { public FloatParameter postExposure; public ClampedFloatParameter contrast, saturation; public ColorParameter colorFilter; }
    public sealed class Vignette : VolumeComponent { public ClampedFloatParameter intensity, smoothness; public ColorParameter color; }

    public abstract class ScriptableRendererData : ScriptableObject { }
    public enum RenderingMode { Forward = 0, ForwardPlus = 2, Deferred = 1 }
    public class PostProcessData : ScriptableObject { }
    public class UniversalRendererData : ScriptableRendererData { public PostProcessData postProcessData; public RenderingMode renderingMode { get; set; } }
    public enum UpscalingFilterSelection { Auto, Linear, Point, FSR, STP }
    public enum LightRenderingMode { Disabled = 0, PerVertex = 2, PerPixel = 1 }
    public class UniversalRenderPipelineAsset : RenderPipelineAsset
    {
        protected override RenderPipeline CreatePipeline() => null;
        public static UniversalRenderPipelineAsset Create(ScriptableRendererData rendererData = null) => null;
        public float renderScale { get; set; }
        public int msaaSampleCount { get; set; }
        public bool supportsHDR { get; set; }
        public float shadowDistance { get; set; }
        public int shadowCascadeCount { get; set; }
        public int mainLightShadowmapResolution { get; set; }
        public int maxAdditionalLightsCount { get; set; }
        public bool supportsCameraDepthTexture { get; set; }
        public bool supportsCameraOpaqueTexture { get; set; }
        public UpscalingFilterSelection upscalingFilter { get; set; }
    }
    public enum AntialiasingMode { None, FastApproximateAntialiasing, SubpixelMorphologicalAntiAliasing, TemporalAntiAliasing }
    public class UniversalAdditionalCameraData : MonoBehaviour { public bool renderPostProcessing { get; set; } public bool renderShadows { get; set; } public AntialiasingMode antialiasing { get; set; } }
    public static class CameraExtensions { public static UniversalAdditionalCameraData GetUniversalAdditionalCameraData(this Camera camera) => null; }
}

namespace UnityEditor
{
    public abstract class BaseShaderGUI : ShaderGUI
    {
        public static void SetMaterialKeywords(Material material, Action<Material> shadingModelFunc = null, Action<Material> shaderFunc = null) { }
    }
}

namespace UnityEditor.Rendering.Universal.ShaderGUI
{
    public static class LitGUI { public static void SetMaterialKeywords(Material material) { } }
    public static class ParticleGUI { public static void SetMaterialKeywords(Material material) { } }
}
