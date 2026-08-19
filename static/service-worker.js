// খুবই ছোট service worker - শুধু PWA installable হওয়ার শর্ত পূরণ করার জন্য।
// ইচ্ছাকৃতভাবে কোনো aggressive caching নেই, কারণ চ্যাট অ্যাপের জন্য সবসময়
// সর্বশেষ ভার্সন দরকার (Render redeploy করলে যেন পুরনো কপি আটকে না থাকে)।

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // কোনো cache নেই, সরাসরি নেটওয়ার্কে পাঠিয়ে দেওয়া হয় - শুধু presence-ই দরকার।
});
