// Mirror-like reflections in the rain puddles (High quality only).
// Drawn as a thin transparent layer over the wet floor. The reflection itself is rendered by
// PlanarReflection.cs into _CatsReflectionTex; the puddle shape comes from the floor's mask
// texture (alpha = smoothness), so reflections appear exactly where the tiles hold water.
Shader "Cats/PuddleReflection"
{
    Properties
    {
        _MaskTex ("Wet mask (A = smoothness)", 2D) = "white" {}
        _NormalTex ("Normal map", 2D) = "bump" {}
        _Tint ("Tint", Color) = (1, 1, 1, 1)
        _Strength ("Strength", Range(0, 1.5)) = 0.9
        _Distortion ("Ripple distortion", Range(0, 0.1)) = 0.025
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent-10" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Pass
        {
            Name "PuddleReflection"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Cull Back
            Offset -1, -1

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_MaskTex);            SAMPLER(sampler_MaskTex);
            TEXTURE2D(_NormalTex);          SAMPLER(sampler_NormalTex);
            TEXTURE2D(_CatsReflectionTex);  SAMPLER(sampler_CatsReflectionTex);

            CBUFFER_START(UnityPerMaterial)
                float4 _MaskTex_ST;
                float4 _NormalTex_ST;
                half4 _Tint;
                half _Strength;
                half _Distortion;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float4 screenPos : TEXCOORD1;
                float3 positionWS : TEXCOORD2;
                half fogFactor : TEXCOORD3;
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.uv = TRANSFORM_TEX(v.uv, _MaskTex);
                o.screenPos = ComputeScreenPos(p.positionCS);
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half smooth = SAMPLE_TEXTURE2D(_MaskTex, sampler_MaskTex, i.uv).a;
                half puddle = saturate((smooth - 0.55h) * 3.0h);
                half wet = saturate(smooth * 1.4h - 0.35h);

                half3 n = UnpackNormal(SAMPLE_TEXTURE2D(_NormalTex, sampler_NormalTex, i.uv));
                float2 suv = i.screenPos.xy / i.screenPos.w;
                suv += n.xy * _Distortion * (1.0h - puddle * 0.8h);
                half3 refl = SAMPLE_TEXTURE2D(_CatsReflectionTex, sampler_CatsReflectionTex, suv).rgb * _Tint.rgb;

                float3 viewDir = normalize(GetWorldSpaceViewDir(i.positionWS));
                half fresnel = 0.12h + 0.88h * pow(1.0h - saturate((half)viewDir.y), 4.0h);
                half alpha = saturate((puddle * 0.85h + wet * 0.25h) * fresnel * _Strength);

                refl = MixFog(refl, i.fogFactor);
                return half4(refl, alpha);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
