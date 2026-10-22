using UnityEngine;

namespace Cats
{
    /// <summary>Baron, the grey cat on the neighbour's balcony: looks at the player and tells the goal.</summary>
    [RequireComponent(typeof(SphereCollider))]
    public class NpcCat : MonoBehaviour, IMeowListener
    {
        public AudioClip meow;
        [TextArea]
        public string[] meowReplies =
        {
            "Мрр? И тебе доброй ночи.",
            "Не кричи, синьора Роза проснётся.",
            "Мяу-мяу. Беги уже, рыба ждёт!",
        };
        AudioSource _audio;
        int _reply;
        float _lastReply = -10f;

        public Vector3 Position => transform.position;

        public void OnMeow(CatController cat, float distance)
        {
            if (Time.time - _lastReply < 3f) return;
            _lastReply = Time.time;
            if (meow != null && _audio != null) _audio.PlayOneShot(meow, 0.9f);
            if (distance < 6f && meowReplies.Length > 0)
                GameManager.Instance?.Say(displayName, meowReplies[_reply++ % meowReplies.Length], 3f);
        }

        void OnDestroy() => MeowListeners.Remove(this);
        public string displayName = "Барон";
        [TextArea]
        public string[] lines =
        {
            "Мяу! Не спится, полосатый?",
            "У причала рыбаки разбирают ночной улов. Успеешь — будет пир.",
            "Иди по карнизу и прыгай туда, где светятся лапки.",
            "Только не урони горшки синьоры Розы!",
        };
        public float secondsPerLine = 3.6f;
        public Transform head;

        CatController _listener;
        int _line = -1;
        float _next;
        Quaternion _headRest;
        bool _done;

        void Start()
        {
            MeowListeners.Add(this);
            _audio = gameObject.AddComponent<AudioSource>();
            _audio.spatialBlend = 1f;
            _audio.minDistance = 1.5f;
            _audio.maxDistance = 25f;
            if (head == null) head = FindDeep(transform.parent != null ? transform.parent : transform, "Head");
            if (head != null) _headRest = head.localRotation;
        }

        static Transform FindDeep(Transform root, string name)
        {
            foreach (Transform c in root)
            {
                if (c.name == name) return c;
                var r = FindDeep(c, name);
                if (r != null) return r;
            }
            return null;
        }

        void OnTriggerEnter(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat == null) return;
            _listener = cat;
            if (!_done && _line < 0) { _line = 0; _next = 0f; }
            var anim = cat.GetComponent<CatAnimator>();
            if (anim != null) anim.LookAt(transform);
        }

        void OnTriggerExit(Collider other)
        {
            var cat = other.GetComponent<CatController>();
            if (cat == null || cat != _listener) return;
            var anim = cat.GetComponent<CatAnimator>();
            if (anim != null) anim.LookAt(null);
            _listener = null;
        }

        void Update()
        {
            if (_listener != null && !_done && _line >= 0 && Time.time >= _next)
            {
                if (_line < lines.Length)
                {
                    GameManager.Instance?.Say(displayName, lines[_line], secondsPerLine);
                    _line++;
                    _next = Time.time + secondsPerLine;
                }
                else _done = true;
            }
        }

        void LateUpdate()
        {
            if (head == null) return;
            var want = _headRest;
            if (_listener != null)
            {
                var local = head.parent.InverseTransformPoint(_listener.transform.position + Vector3.up * 0.25f);
                float yaw = Mathf.Clamp(Mathf.Atan2(local.x, local.z) * Mathf.Rad2Deg, -70f, 70f);
                want = _headRest * Quaternion.Euler(0f, yaw, 0f);
            }
            else
            {
                want = _headRest * Quaternion.Euler(0f, Mathf.Sin(Time.time * 0.3f) * 25f, 0f);
            }
            head.localRotation = Quaternion.Slerp(head.localRotation, want, 1f - Mathf.Exp(-Time.deltaTime * 4f));
        }
    }
}
