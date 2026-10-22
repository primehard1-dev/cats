using UnityEngine;

namespace Cats
{
    /// <summary>A flower pot the cat can push off a ledge. It shatters, and Signora Rosa is not amused.</summary>
    [RequireComponent(typeof(Rigidbody))]
    public class PotBreaker : MonoBehaviour
    {
        public AudioClip breakClip;
        public Material shardMaterial;
        public float breakSpeed = 2.5f;
        bool _broken;

        void OnCollisionEnter(Collision c)
        {
            if (_broken || c.relativeVelocity.magnitude < breakSpeed) return;
            if (c.collider.GetComponent<CatController>() != null) return;
            _broken = true;
            if (breakClip != null) AudioSource.PlayClipAtPoint(breakClip, transform.position, CatsVolume.Sfx);
            SaveSystem.Data.potsBroken++;
            for (int i = 0; i < 7; i++)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Cube);
                s.name = "Shard";
                s.transform.position = transform.position + Random.insideUnitSphere * 0.08f + Vector3.up * 0.1f;
                s.transform.rotation = Random.rotation;
                s.transform.localScale = new Vector3(Random.Range(0.03f, 0.08f), 0.015f, Random.Range(0.03f, 0.07f));
                if (shardMaterial != null) s.GetComponent<Renderer>().sharedMaterial = shardMaterial;
                var rb = s.AddComponent<Rigidbody>();
                rb.mass = 0.05f;
                rb.AddForce(Random.insideUnitSphere * 0.4f + Vector3.up * 0.3f, ForceMode.Impulse);
                Destroy(s, 12f);
            }
            if (GameManager.Instance != null)
                GameManager.Instance.Say("Синьора Роза", "Эй! Опять эти кошки! Мои герани!", 3f);
            Destroy(gameObject);
        }
    }
}
