using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Cats
{
    /// <summary>
    /// Planar reflection for the puddles: a mirrored camera renders the scene (at half resolution)
    /// into _CatsReflectionTex for the closest <see cref="PuddleSurface"/>. High quality only.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    [DefaultExecutionOrder(1000)]
    public class PlanarReflection : MonoBehaviour
    {
        public LayerMask reflectLayers = ~0;
        [Range(0.25f, 1f)] public float resolutionScale = 0.5f;
        [Tooltip("The reflection is rendered only when the camera is this close to a wet floor.")]
        public float activationDistance = 12f;
        public float farClip = 500f;

        static readonly int ReflectionTex = Shader.PropertyToID("_CatsReflectionTex");

        Camera _main, _refl;
        RenderTexture _rt;
        PuddleSurface _active;

        void Start()
        {
            _main = GetComponent<Camera>();
            foreach (var s in PuddleSurface.All) s.SetVisible(false);
            if (!QualityTier.IsHigh)
            {
                enabled = false;
                return;
            }
            var go = new GameObject("ReflectionCamera");
            go.hideFlags = HideFlags.DontSave;
            _refl = go.AddComponent<Camera>();
            _refl.CopyFrom(_main);
            _refl.depth = _main.depth - 1f;
            _refl.cullingMask = reflectLayers;
            _refl.farClipPlane = farClip;
            _refl.allowMSAA = false;
            _refl.enabled = false;
            var data = _refl.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = false;
            data.renderShadows = false;
            data.antialiasing = AntialiasingMode.None;
        }

        void OnEnable()
        {
            RenderPipelineManager.beginCameraRendering += OnBegin;
            RenderPipelineManager.endCameraRendering += OnEnd;
        }

        void OnDisable()
        {
            RenderPipelineManager.beginCameraRendering -= OnBegin;
            RenderPipelineManager.endCameraRendering -= OnEnd;
            if (_refl != null) _refl.enabled = false;
        }

        void OnDestroy()
        {
            if (_rt != null) _rt.Release();
            if (_refl != null) Destroy(_refl.gameObject);
        }

        void OnBegin(ScriptableRenderContext ctx, Camera cam) { if (cam == _refl) GL.invertCulling = true; }
        void OnEnd(ScriptableRenderContext ctx, Camera cam) { if (cam == _refl) GL.invertCulling = false; }

        void LateUpdate()
        {
            if (_refl == null) return;
            var camPos = _main.transform.position;
            PuddleSurface best = null;
            float bestD = activationDistance;
            foreach (var s in PuddleSurface.All)
            {
                if (s.Height > camPos.y - 0.2f) continue;
                float d = s.DistanceTo(camPos);
                if (d < bestD) { bestD = d; best = s; }
            }
            if (best != _active)
            {
                foreach (var s in PuddleSurface.All) s.SetVisible(s == best);
                _active = best;
            }
            if (_active == null) { _refl.enabled = false; return; }

            EnsureTarget();
            float h = _active.Height;
            var plane = new Vector4(0f, 1f, 0f, -h);
            var mirror = ReflectionMatrix(plane);
            _refl.fieldOfView = _main.fieldOfView;
            _refl.aspect = _main.aspect;
            _refl.transform.position = mirror.MultiplyPoint(camPos);
            var fwd = Vector3.Reflect(_main.transform.forward, Vector3.up);
            var up = Vector3.Reflect(_main.transform.up, Vector3.up);
            _refl.transform.rotation = Quaternion.LookRotation(fwd, up);
            _refl.worldToCameraMatrix = _main.worldToCameraMatrix * mirror;
            var clip = CameraSpacePlane(_refl.worldToCameraMatrix, new Vector3(0f, h, 0f), Vector3.up);
            _refl.projectionMatrix = _main.CalculateObliqueMatrix(clip);
            _refl.targetTexture = _rt;
            _refl.enabled = true;
            Shader.SetGlobalTexture(ReflectionTex, _rt);
        }

        void EnsureTarget()
        {
            int w = Mathf.Max(64, (int)(Screen.width * resolutionScale));
            int hgt = Mathf.Max(64, (int)(Screen.height * resolutionScale));
            if (_rt != null && _rt.width == w && _rt.height == hgt) return;
            if (_rt != null) _rt.Release();
            var fmt = SystemInfo.SupportsRenderTextureFormat(RenderTextureFormat.ARGBHalf) ? RenderTextureFormat.ARGBHalf : RenderTextureFormat.Default;
            _rt = new RenderTexture(w, hgt, 24, fmt) { name = "PuddleReflection", filterMode = FilterMode.Bilinear, useMipMap = false };
            _rt.Create();
        }

        static Vector4 CameraSpacePlane(Matrix4x4 worldToCamera, Vector3 pos, Vector3 normal, float offset = 0.02f)
        {
            var cpos = worldToCamera.MultiplyPoint(pos + normal * offset);
            var cnormal = worldToCamera.MultiplyVector(normal).normalized;
            return new Vector4(cnormal.x, cnormal.y, cnormal.z, -Vector3.Dot(cpos, cnormal));
        }

        static Matrix4x4 ReflectionMatrix(Vector4 p)
        {
            var m = Matrix4x4.identity;
            m.m00 = 1f - 2f * p.x * p.x; m.m01 = -2f * p.x * p.y; m.m02 = -2f * p.x * p.z; m.m03 = -2f * p.w * p.x;
            m.m10 = -2f * p.y * p.x; m.m11 = 1f - 2f * p.y * p.y; m.m12 = -2f * p.y * p.z; m.m13 = -2f * p.w * p.y;
            m.m20 = -2f * p.z * p.x; m.m21 = -2f * p.z * p.y; m.m22 = 1f - 2f * p.z * p.z; m.m23 = -2f * p.w * p.z;
            m.m30 = 0f; m.m31 = 0f; m.m32 = 0f; m.m33 = 1f;
            return m;
        }
    }
}
