using UnityEngine;
using UnityEngine.UI;

namespace Cats
{
    /// <summary>Fade overlay, hints at the top, dialogue box at the bottom, finish panel.</summary>
    public class GameUI : MonoBehaviour
    {
        public CanvasGroup fade;
        public Text hintText;
        public CanvasGroup hintGroup;
        public Text dialogueName;
        public Text dialogueText;
        public CanvasGroup dialogueGroup;
        public CanvasGroup finishGroup;
        public Text finishText;
        public GameObject touchControls;

        float _hintUntil, _dialogueUntil, _fadeTarget, _fadeSpeed = 2f;

        void Awake()
        {
            if (fade != null) fade.alpha = 1f;
            if (hintGroup != null) hintGroup.alpha = 0f;
            if (dialogueGroup != null) dialogueGroup.alpha = 0f;
            if (finishGroup != null) finishGroup.alpha = 0f;
        }

        public void FadeTo(float alpha, float seconds)
        {
            _fadeTarget = alpha;
            _fadeSpeed = 1f / Mathf.Max(0.01f, seconds);
        }

        public bool FadeDone => fade == null || Mathf.Approximately(fade.alpha, _fadeTarget);

        public void ShowHint(string text, float seconds)
        {
            if (hintText == null) return;
            hintText.text = text;
            _hintUntil = Time.time + seconds;
        }

        public void ShowDialogue(string speaker, string text, float seconds)
        {
            if (dialogueText == null) return;
            if (dialogueName != null) dialogueName.text = speaker;
            dialogueText.text = text;
            _dialogueUntil = Time.time + seconds;
        }

        public void ShowFinish(string text)
        {
            if (finishText != null) finishText.text = text;
            if (finishGroup != null) finishGroup.alpha = 1f;
            if (touchControls != null) touchControls.SetActive(false);
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            if (fade != null) fade.alpha = Mathf.MoveTowards(fade.alpha, _fadeTarget, _fadeSpeed * dt);
            if (hintGroup != null) hintGroup.alpha = Mathf.MoveTowards(hintGroup.alpha, Time.time < _hintUntil ? 1f : 0f, dt * 3f);
            if (dialogueGroup != null)
                dialogueGroup.alpha = Mathf.MoveTowards(dialogueGroup.alpha, Time.time < _dialogueUntil ? 1f : 0f, dt * 4f);
        }
    }
}
