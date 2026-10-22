using System.Collections.Generic;
using UnityEngine;

namespace Cats
{
    /// <summary>Something in the world that reacts when a cat meows nearby (Baron answers, pigeons fly away).</summary>
    public interface IMeowListener
    {
        Vector3 Position { get; }
        void OnMeow(CatController cat, float distance);
    }

    public static class MeowListeners
    {
        static readonly List<IMeowListener> All = new List<IMeowListener>();
        public const float HearingRadius = 9f;

        public static void Add(IMeowListener l) { if (!All.Contains(l)) All.Add(l); }
        public static void Remove(IMeowListener l) => All.Remove(l);

        public static void Notify(CatController cat, Vector3 from)
        {
            for (int i = All.Count - 1; i >= 0; i--)
            {
                float d = Vector3.Distance(All[i].Position, from);
                if (d <= HearingRadius) All[i].OnMeow(cat, d);
            }
        }
    }
}
