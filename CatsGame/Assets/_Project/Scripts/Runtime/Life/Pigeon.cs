using UnityEngine;

namespace Cats
{
    /// <summary>Pigeon on a roof: pecks and coos, flies off when the cat comes close or meows, returns later.</summary>
    public class Pigeon : MonoBehaviour, IMeowListener
    {
        public float scareRadius = 2.2f;
        public float returnAfter = 25f;
        public AudioClip flap, coo;
        public Transform cat;

        Transform _body, _head, _wingL, _wingR;
        Vector3 _home;
        Quaternion _homeRot;
        Vector3 _flyDir;
        float _flyTime = -1f, _gone, _nextPeck, _peck, _nextCoo;
        AudioSource _audio;
        Transform _cat;

        public Vector3 Position => transform.position;

        void Start()
        {
            _body = Find("Body");
            _head = Find("Head");
            _wingL = Find("WingL");
            _wingR = Find("WingR");
            _home = transform.position;
            _homeRot = transform.rotation;
            _audio = gameObject.AddComponent<AudioSource>();
            _audio.spatialBlend = 1f;
            _audio.minDistance = 1f;
            _audio.maxDistance = 18f;
            _audio.rolloffMode = AudioRolloffMode.Linear;
            _nextCoo = Time.time + Random.Range(3f, 12f);
            _cat = cat;
            MeowListeners.Add(this);
        }

        void OnDestroy() => MeowListeners.Remove(this);

        Transform Find(string n)
        {
            foreach (var t in GetComponentsInChildren<Transform>()) if (t.name == n) return t;
            return null;
        }

        public void OnMeow(CatController cat, float distance)
        {
            if (distance < 7f) FlyAway(cat.transform.position);
        }

        void FlyAway(Vector3 from)
        {
            if (_flyTime >= 0f) return;
            var away = transform.position - from;
            away.y = 0f;
            if (away.sqrMagnitude < 0.01f) away = Random.insideUnitSphere;
            _flyDir = (away.normalized + Vector3.up * 0.7f + Random.insideUnitSphere * 0.3f).normalized;
            _flyTime = 0f;
            if (flap != null) _audio.PlayOneShot(flap, 0.8f * CatsVolume.Sfx);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            if (_flyTime >= 0f)
            {
                _flyTime += dt;
                transform.position += _flyDir * (2f + _flyTime * 4f) * dt;
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(new Vector3(_flyDir.x, 0f, _flyDir.z)), dt * 5f);
                float flapAngle = Mathf.Sin(Time.time * 40f) * 55f;
                if (_wingL != null) _wingL.localRotation = Quaternion.Euler(0f, 0f, flapAngle);
                if (_wingR != null) _wingR.localRotation = Quaternion.Euler(0f, 0f, -flapAngle);
                if (_flyTime > 6f)
                {
                    _flyTime = -1f;
                    _gone = Time.time;
                    SetVisible(false);
                }
                return;
            }
            if (_gone > 0f)
            {
                bool catFar = _cat == null || Vector3.Distance(_cat.position, _home) > 12f;
                if (Time.time - _gone > returnAfter && catFar)
                {
                    _gone = 0f;
                    transform.SetPositionAndRotation(_home, _homeRot);
                    if (_wingL != null) _wingL.localRotation = Quaternion.identity;
                    if (_wingR != null) _wingR.localRotation = Quaternion.identity;
                    SetVisible(true);
                }
                return;
            }
            if (_cat != null && Vector3.Distance(_cat.position, transform.position) < scareRadius) { FlyAway(_cat.position); return; }

            // idle: peck now and then, coo sometimes
            if (Time.time > _nextPeck) { _peck = 1f; _nextPeck = Time.time + Random.Range(1.5f, 5f); }
            _peck = Mathf.MoveTowards(_peck, 0f, dt * 3f);
            if (_body != null) _body.localRotation = Quaternion.Euler(Mathf.Sin(_peck * Mathf.PI) * 35f, 0f, 0f);
            if (Time.time > _nextCoo && coo != null) { _audio.PlayOneShot(coo, 0.5f * CatsVolume.Sfx); _nextCoo = Time.time + Random.Range(8f, 20f); }
        }

        void SetVisible(bool v)
        {
            foreach (var r in GetComponentsInChildren<Renderer>()) r.enabled = v;
        }
    }
}
