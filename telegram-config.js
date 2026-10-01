// Fill these after creating ad blocks in AdsGram partner dashboard.
// GitHub Pages is static, so these IDs are public by design; never place secret API tokens here.
window.KOLEYA_TG_CONFIG = {
  rewardBlockId: "51166",     // Rewarded block ID from AdsGram
  interstitialBlockId: "",    // Interstitial block, normally int-XXX
  useInterstitial: false,      // Start with rewarded only; enable later if desired
  requestFullscreen: true,
  leaderboardApiUrl: "",      // Cloudflare Worker URL, added before v1.1.0 release

  // Safety: rewards are NEVER granted without a successful ad by default.
  // For local UI testing only: set true and open index.html?devads=1
  devRewardWithoutAd: false
};
