using System;
using UnityEngine;

namespace Cats.EditorTools
{
    // Mirrors CatsGame/Assets/_Project/Data/*.json written by tools/level/*.py (JsonUtility friendly).

    [Serializable] public class MaterialDef
    {
        public string name, shader, albedo, normal, mask, emission;
        public Color color = Color.white;
        public Vector2 tiling = Vector2.one;
        public float smoothness, metallic, normalScale = 1f, cutoff;
        public Color emissionColor;
        public bool doubleSided;
    }

    [Serializable] public class MaterialLibraryData { public MaterialDef[] materials; }

    [Serializable] public class BlockData
    {
        public string name, mat, surface;
        public Vector3 pos, size, rot;
        public bool visible, collide, isStatic;
    }

    [Serializable] public class RoofData { public Vector3 pos, size; public float rotY; public string mat, gable; }

    [Serializable] public class PropLight { public Color color; public float intensity, range; public string mode; public bool shadows; }

    [Serializable] public class PropData
    {
        public string model, collider, matSwap;
        public Vector3 pos, scale;
        public float rotY;
        public bool isStatic;
        public PropLight light;
    }

    [Serializable] public class LightData
    {
        public string name, type, mode;
        public Vector3 pos;
        public Color color;
        public float intensity, range;
        public bool shadows;
    }

    [Serializable] public class MarkerData { public Vector3 pos; }
    [Serializable] public class BoxData { public Vector3 pos, size; }
    [Serializable] public class CheckpointData { public string id; public Vector3 pos, size; public float spawnRotY; }

    [Serializable] public class CameraZoneData
    {
        public Vector3 pos, size;
        public float distance, height, pitch, side;
    }

    [Serializable] public class RopeData { public Vector3[] points; public float sag, width; }
    [Serializable] public class ProbeData { public Vector3 pos, size; public int importance; }

    [Serializable] public class HouseData
    {
        public Vector3 pos, size;
        public string mat, roofMat;
        public bool gable;
        public float uvOffset, foundation;
    }

    [Serializable] public class GarlandData { public Vector3 a, b; public float sag, bulbSpacing; public bool gameplay; }

    [Serializable] public class MoonData { public float azimuth, elevation, intensity, quadDistance, quadSize; public Color color; }

    [Serializable] public class EnvData
    {
        public Color ambientSky, ambientEquator, ambientGround, fogColor;
        public float fogStart, fogEnd;
    }

    [Serializable] public class SpawnData { public Vector3 p1, p2; public float rotY; }
    [Serializable] public class CamPose { public Vector3 pos, lookAt; }
    [Serializable] public class NpcData { public string model; public Vector3 pos; public float rotY, radius; }
    [Serializable] public class SeaData { public float y; public Vector3 center, size; }
    [Serializable] public class BackgroundData { public float radius, height, y, arcStart, arcEnd; }

    [Serializable] public class DecalData { public string mat; public Vector3 a, b, c, d; public Vector2 uv; }
    [Serializable] public class PigeonData { public Vector3 pos; public float rotY; }
    [Serializable] public class SoundData { public string clip; public Vector3 pos; public float volume, minDistance, maxDistance; }
    [Serializable] public class PointData { public Vector3 pos; }

    [Serializable] public class LevelData
    {
        public string name;
        public MoonData moon;
        public EnvData environment;
        public SpawnData spawn;
        public CamPose startCamera;
        public NpcData npc;
        public BoxData exit;
        public SeaData sea;
        public BackgroundData background;
        public BlockData[] blocks;
        public RoofData[] roofs;
        public PropData[] props;
        public LightData[] lights;
        public MarkerData[] markers;
        public CheckpointData[] checkpoints;
        public BoxData[] killZones;
        public CameraZoneData[] cameraZones;
        public RopeData[] ropes;
        public BoxData[] ledgeZones;
        public ProbeData[] reflectionProbes;
        public HouseData[] houses;
        public GarlandData[] garlands;
        public Vector3[] lightProbes;
        public DecalData[] decals;
        public PigeonData[] pigeons;
        public BoxData[] fireflies, drips, ripples;
        public PointData[] tvLights;
        public SoundData[] sounds;

        public Vector3 MoonDirection
        {
            get
            {
                float az = moon.azimuth * Mathf.Deg2Rad, el = moon.elevation * Mathf.Deg2Rad;
                return new Vector3(Mathf.Sin(az) * Mathf.Cos(el), Mathf.Sin(el), Mathf.Cos(az) * Mathf.Cos(el));
            }
        }
    }
}
