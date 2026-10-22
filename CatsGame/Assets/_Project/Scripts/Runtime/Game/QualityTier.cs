using UnityEngine;

namespace Cats
{
    /// <summary>Picks the Low or High quality level (URP asset) from the device capabilities.</summary>
    public static class QualityTier
    {
        public static bool IsHigh { get; private set; }

        public static void Apply()
        {
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            bool high = SystemInfo.systemMemorySize >= 6000 && SystemInfo.processorCount >= 8 &&
                        SystemInfo.graphicsMemorySize >= 1500;
            if (!Application.isMobilePlatform) high = true;
            IsHigh = high;
            int count = QualitySettings.names.Length;
            if (count > 0) QualitySettings.SetQualityLevel(high ? count - 1 : 0, true);
            Application.targetFrameRate = high ? 60 : 30;
        }
    }
}
