using UnityEngine;

namespace Cats
{
    /// <summary>Paw steps (soft on tiles, metallic on AC units), jump, landing, meow, purring when sitting.</summary>
    [RequireComponent(typeof(CatController))]
    public class CatAudio : MonoBehaviour
    {
        public AudioClip[] steps;
        public AudioClip stepMetal;
        public AudioClip jump;
        public AudioClip land;
        public AudioClip[] meows;
        public AudioClip purrLoop;
        public AudioClip ropeCreak;
        public float stepDistance = 0.21f;

        CatController _cat;
        CatAnimator _anim;
        AudioSource _fx, _purr;
        Vector3 _last;
        float _travel, _creakTimer;

        void Awake()
        {
            _cat = GetComponent<CatController>();
            _anim = GetComponent<CatAnimator>();
            _fx = gameObject.AddComponent<AudioSource>();
            _fx.spatialBlend = 0.6f;
            _fx.playOnAwake = false;
            _purr = gameObject.AddComponent<AudioSource>();
            _purr.clip = purrLoop;
            _purr.loop = true;
            _purr.volume = 0f;
            _purr.spatialBlend = 0.5f;
            _last = transform.position;
        }

        void OnEnable()
        {
            _cat.Jumped += OnJump;
            _cat.Landed += OnLand;
            _cat.Meowed += Meow;
        }

        void OnDisable()
        {
            _cat.Jumped -= OnJump;
            _cat.Landed -= OnLand;
            _cat.Meowed -= Meow;
        }

        void OnJump() => Play(jump, 0.35f, 1f + Random.Range(-0.1f, 0.1f));
        void OnLand() => Play(land, 0.6f, 1f + Random.Range(-0.08f, 0.08f));

        public void Meow()
        {
            if (meows == null || meows.Length == 0) return;
            Play(meows[Random.Range(0, meows.Length)], 0.9f, Random.Range(0.95f, 1.08f));
            if (_anim != null) _anim.PlayMeow();
            MeowListeners.Notify(_cat, transform.position);
            SaveSystem.Data.meows++;
        }

        void Play(AudioClip clip, float volume, float pitch)
        {
            if (clip == null) return;
            _fx.pitch = pitch;
            _fx.PlayOneShot(clip, volume * CatsVolume.Sfx);
        }

        void Update()
        {
            var pos = transform.position;
            var d = pos - _last;
            d.y = 0f;
            _last = pos;
            bool walking = _cat.IsGrounded && _cat.CurrentState == CatController.State.Normal;
            if (walking || _cat.CurrentState == CatController.State.Rope)
            {
                _travel += d.magnitude;
                if (_travel > stepDistance)
                {
                    _travel = 0f;
                    var g = _cat.Ground;
                    bool metal = g != null && (g.name.StartsWith("AC") || g.name.Contains("Collider"));
                    if (_cat.CurrentState == CatController.State.Rope) { }
                    else if (metal && stepMetal != null) Play(stepMetal, 0.25f, Random.Range(0.9f, 1.1f));
                    else if (steps != null && steps.Length > 0) Play(steps[Random.Range(0, steps.Length)], 0.3f, Random.Range(0.9f, 1.15f));
                }
            }
            if (_cat.CurrentState == CatController.State.Rope && ropeCreak != null)
            {
                _creakTimer -= Time.deltaTime;
                if (_creakTimer <= 0f && _cat.Velocity.sqrMagnitude > 0.01f)
                {
                    Play(ropeCreak, 0.25f, Random.Range(0.85f, 1.15f));
                    _creakTimer = Random.Range(0.8f, 1.6f);
                }
            }

            bool sitting = _anim != null && _anim.IsSitting;
            float target = sitting && _anim.SitTime > 2.5f ? 0.45f * CatsVolume.Sfx : 0f;
            _purr.volume = Mathf.MoveTowards(_purr.volume, target, Time.deltaTime * 0.3f);
            if (_purr.volume > 0f && !_purr.isPlaying && purrLoop != null) _purr.Play();
            else if (_purr.volume <= 0f && _purr.isPlaying) _purr.Stop();
        }
    }
}
