# 🧪 PWA Testing Guide - MLBB Coach AI

## 🎯 Testing Strategy Overview

This guide provides comprehensive testing procedures for validating PWA functionality across different devices, browsers, and scenarios.

## 🚀 Quick Start Testing

### **1. Automated PWA Test Suite**

Run the built-in test suite to check all PWA features:

```javascript
// Open browser console and run:
await window.pwaTestSuite.runAllTests();

// Or run quick validation:
await window.pwaTestSuite.runQuickTest();

// View detailed test report:
window.pwaTestSuite.displayTestReport();
```

### **2. Manual Testing Checklist**

#### **✅ Core PWA Features**

- [ ] Service Worker registers successfully
- [ ] App works offline (disconnect network and test)
- [ ] Web App Manifest loads correctly
- [ ] App can be installed ("Add to Home Screen")
- [ ] Push notifications work (if permissions granted)

#### **✅ Mobile Experience**

- [ ] Touch interactions work smoothly
- [ ] UI is responsive across screen sizes
- [ ] Camera capture works on mobile devices
- [ ] Bottom navigation is accessible
- [ ] Safe areas are handled correctly (iPhone notch)

## 📱 Device-Specific Testing

### **iOS Testing (Safari)**

#### **Prerequisites:**

- iOS 11.3+ (PWA support)
- Safari browser
- HTTPS connection (required for PWA features)

#### **Test Steps:**

1. **Open in Safari**: Navigate to your MLBB Coach AI URL
2. **Install Test**:
   - Tap Share button (⎙)
   - Tap "Add to Home Screen"
   - Confirm installation
   - Test app from home screen
3. **Offline Test**:
   - Turn on Airplane Mode
   - Open app from home screen
   - Verify offline functionality
4. **Camera Test**:
   - Try screenshot capture feature
   - Grant camera permissions
   - Test photo capture and upload

#### **iOS-Specific Features:**

```javascript
// Check iOS PWA status
console.log("iOS Standalone:", window.navigator.standalone);
console.log(
  "Display Mode:",
  window.matchMedia("(display-mode: standalone)").matches
);
```

### **Android Testing (Chrome)**

#### **Prerequisites:**

- Android 5.0+ with Chrome 76+
- HTTPS connection

#### **Test Steps:**

1. **Install Prompt Test**:
   - Visit site in Chrome
   - Look for install banner/prompt
   - Test "Add to Home Screen" from menu
2. **WebAPK Test**:
   - Install app and wait for WebAPK generation
   - Check if app runs as WebAPK (standalone mode)
3. **Background Sync Test**:
   - Go offline while using app
   - Perform actions (upload screenshot, etc.)
   - Go back online and verify sync

#### **Android-Specific Features:**

```javascript
// Check Android PWA features
console.log("Install Prompt Available:", !!window.deferredPrompt);
console.log(
  "Background Sync:",
  "serviceWorker" in navigator &&
    "sync" in window.ServiceWorkerRegistration.prototype
);
```

### **Desktop Testing**

#### **Chrome Desktop:**

```bash
# Enable PWA debugging
chrome --enable-features=DesktopPWAs --user-data-dir=/tmp/chrome-pwa
```

#### **Test Steps:**

1. **Install from Omnibox**: Look for install icon in address bar
2. **App Window**: Test standalone app window
3. **Keyboard Navigation**: Test accessibility with keyboard
4. **Window Management**: Test minimize, maximize, close

## 🛠️ Development Testing Tools

### **1. Chrome DevTools PWA Auditing**

#### **Lighthouse PWA Audit:**

1. Open Chrome DevTools (F12)
2. Go to "Lighthouse" tab
3. Select "Progressive Web App" category
4. Run audit and aim for 90+ score

#### **Application Tab Testing:**

1. **Service Workers**: Check registration and status
2. **Storage**: Inspect Cache Storage, IndexedDB, Local Storage
3. **Manifest**: Validate manifest.json
4. **Background Services**: Monitor background sync events

### **2. PWA Testing Commands**

Add these to your development workflow:

```bash
# Install PWA testing tools
npm install -g lighthouse pwa-asset-generator workbox-cli

# Run Lighthouse PWA audit
lighthouse https://your-domain.com --only-categories=pwa --view

# Generate PWA assets
pwa-asset-generator logo.png ./public/images/icons --manifest ./public/manifest.json

# Test service worker
workbox generateSW workbox-config.js
```

### **3. Browser Testing Matrix**

| Browser | Version | PWA Support | Install Method     | Notes             |
| ------- | ------- | ----------- | ------------------ | ----------------- |
| Chrome  | 76+     | Full        | Install prompt     | Best PWA support  |
| Safari  | 11.3+   | Partial     | Add to Home Screen | No install prompt |
| Firefox | 79+     | Partial     | Manual install     | Limited features  |
| Edge    | 79+     | Full        | Install prompt     | Chromium-based    |

## 📊 Automated Testing Scripts

### **1. PWA Health Check Script**

```javascript
// Add to your testing pipeline
async function runPWAHealthCheck() {
  const results = await window.pwaTestSuite.runAllTests();

  const criticalTests = [
    "testServiceWorker",
    "testManifest",
    "testInstallability",
  ];
  const criticalPassed = criticalTests.every((test) => results[test]?.passed);

  if (!criticalPassed) {
    console.error("❌ Critical PWA tests failed!");
    return false;
  }

  console.log("✅ PWA health check passed!");
  return true;
}
```

### **2. Performance Testing**

```javascript
// Test PWA performance
async function testPWAPerformance() {
  // Test cache performance
  const cacheStart = performance.now();
  await caches.match("/");
  const cacheTime = performance.now() - cacheStart;

  // Test offline capability
  const offlineStart = performance.now();
  await caches.match("/offline.html");
  const offlineTime = performance.now() - offlineStart;

  console.log(`Cache retrieval: ${cacheTime.toFixed(2)}ms`);
  console.log(`Offline page: ${offlineTime.toFixed(2)}ms`);

  return {
    cachePerformance: cacheTime < 50, // Should be under 50ms
    offlineReady: offlineTime < 100, // Should be under 100ms
  };
}
```

## 📱 Real Device Testing

### **Testing Devices Matrix**

| Device Type | Recommended Models    | Key Tests                               |
| ----------- | --------------------- | --------------------------------------- |
| **iPhone**  | iPhone 12+, Safari    | Add to Home Screen, standalone mode     |
| **Android** | Pixel, Samsung Galaxy | Install prompt, WebAPK, background sync |
| **Tablet**  | iPad, Android tablet  | Responsive design, touch interactions   |
| **Desktop** | Windows, macOS, Linux | Window management, keyboard navigation  |

### **Network Testing**

#### **Connection Scenarios:**

1. **High-speed WiFi**: Test full functionality
2. **Slow 3G**: Test loading performance and caching
3. **Offline**: Test offline capabilities and sync
4. **Intermittent**: Test connection recovery and background sync

#### **Testing Commands:**

```bash
# Chrome DevTools Network Throttling
# 1. Open DevTools > Network tab
# 2. Select throttling: "Slow 3G", "Offline", etc.
# 3. Test app functionality

# Simulate offline in code:
window.dispatchEvent(new Event('offline'));
// Test offline features

window.dispatchEvent(new Event('online'));
// Test online recovery
```

## 🔧 Debugging PWA Issues

### **Common Issues and Solutions**

#### **1. Service Worker Not Registering**

```javascript
// Debug service worker registration
navigator.serviceWorker
  .register("/sw.js")
  .then((reg) => console.log("SW registered:", reg))
  .catch((err) => console.error("SW registration failed:", err));
```

#### **2. Manifest Issues**

```javascript
// Validate manifest
fetch("/manifest.json")
  .then((response) => response.json())
  .then((manifest) => console.log("Manifest:", manifest))
  .catch((err) => console.error("Manifest error:", err));
```

#### **3. Cache Issues**

```javascript
// Debug cache contents
caches.keys().then((cacheNames) => {
  console.log("Available caches:", cacheNames);
  return Promise.all(
    cacheNames.map(async (cacheName) => {
      const cache = await caches.open(cacheName);
      const requests = await cache.keys();
      console.log(`${cacheName}: ${requests.length} items`);
    })
  );
});
```

#### **4. Installation Issues**

```javascript
// Debug installation readiness
window.addEventListener("beforeinstallprompt", (e) => {
  console.log("Install prompt available:", e);
  // Store for later use
  window.deferredPrompt = e;
});
```

## 📈 Performance Testing

### **Lighthouse CI Integration**

Add to your CI/CD pipeline:

```yaml
# .github/workflows/pwa-test.yml
name: PWA Testing
on: [push, pull_request]

jobs:
  pwa-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: "18"
      - name: Install dependencies
        run: npm install
      - name: Build app
        run: npm run build
      - name: Serve app
        run: npm run serve &
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun
```

### **Performance Thresholds**

| Metric                       | Target | Critical |
| ---------------------------- | ------ | -------- |
| **First Contentful Paint**   | <2s    | <3s      |
| **Largest Contentful Paint** | <2.5s  | <4s      |
| **Time to Interactive**      | <3s    | <5s      |
| **Cumulative Layout Shift**  | <0.1   | <0.25    |
| **PWA Score**                | >90    | >70      |

## 🧪 Testing Scenarios

### **Scenario 1: New User Experience**

1. First visit to site
2. Install prompt handling
3. Permission requests (camera, notifications)
4. Offline functionality discovery
5. Achievement system introduction

### **Scenario 2: Power User Workflow**

1. Daily app usage from home screen
2. Screenshot analysis workflow
3. Achievement progress tracking
4. Learning path completion
5. Social features usage

### **Scenario 3: Network Edge Cases**

1. Poor connectivity (slow 3G)
2. Connection drops during upload
3. Background sync when connection restored
4. Offline data persistence
5. Cache invalidation and updates

### **Scenario 4: Device Capabilities**

1. Camera access and capture
2. Push notification delivery
3. Storage quota management
4. Background app refresh
5. Multi-tab synchronization

## 📋 Testing Checklist

### **Before Production Deployment**

#### **✅ Core PWA Requirements**

- [ ] HTTPS enabled and working
- [ ] Service Worker registered and active
- [ ] Web App Manifest valid and accessible
- [ ] App installable on target platforms
- [ ] Offline functionality working
- [ ] Performance meets targets (Lighthouse score >90)

#### **✅ Mobile Experience**

- [ ] Responsive design works on all screen sizes
- [ ] Touch interactions are smooth and responsive
- [ ] Camera integration works on mobile devices
- [ ] Push notifications deliver successfully
- [ ] App feels native-like when installed

#### **✅ Cross-Platform Compatibility**

- [ ] Works on iOS Safari (iPhone/iPad)
- [ ] Works on Android Chrome
- [ ] Works on desktop browsers
- [ ] Handles different screen orientations
- [ ] Accessibility features work correctly

#### **✅ Performance & Reliability**

- [ ] App loads quickly (<3s on slow 3G)
- [ ] Background sync works reliably
- [ ] No memory leaks or performance degradation
- [ ] Error handling works gracefully
- [ ] Updates deploy and install correctly

## 🔍 Advanced Testing

### **Load Testing PWA Features**

```javascript
// Test concurrent users
async function testConcurrentPWAUsage() {
  const workers = [];

  for (let i = 0; i < 100; i++) {
    workers.push(new Worker("/test-worker.js"));
  }

  // Test service worker under load
  const promises = workers.map(
    (worker) =>
      new Promise((resolve) => {
        worker.postMessage({ action: "testPWA" });
        worker.onmessage = (e) => resolve(e.data);
      })
  );

  const results = await Promise.all(promises);
  console.log("Load test results:", results);
}
```

### **Memory Leak Testing**

```javascript
// Monitor memory usage over time
function monitorMemoryUsage() {
  setInterval(() => {
    if (performance.memory) {
      const memory = performance.memory;
      console.log("Memory Usage:", {
        used: `${(memory.usedJSHeapSize / 1048576).toFixed(2)} MB`,
        total: `${(memory.totalJSHeapSize / 1048576).toFixed(2)} MB`,
        limit: `${(memory.jsHeapSizeLimit / 1048576).toFixed(2)} MB`,
      });
    }
  }, 10000); // Every 10 seconds
}
```

## 📊 Testing Reports

### **Generate Test Report**

```javascript
// Generate comprehensive test report
async function generatePWAReport() {
  const report = {
    timestamp: new Date().toISOString(),
    environment: window.pwaTestSuite.getEnvironmentInfo(),
    testResults: await window.pwaTestSuite.runAllTests(),
    performanceMetrics: await testPWAPerformance(),
    deviceCapabilities: window.deviceIntegration.getCapabilities(),
  };

  // Save report
  localStorage.setItem("pwa-test-report", JSON.stringify(report, null, 2));

  // Display summary
  console.log("📊 PWA Test Report Generated");
  console.log("Overall Status:", report.testResults.summary?.overallStatus);
  console.log("Tests Passed:", report.testResults.summary?.passedTests);

  return report;
}
```

## 🎯 Ready to Test!

Choose your testing approach:

### **Option 1: Quick Validation (5 minutes)**

```bash
# Start your development server
npm run dev

# Open browser console and run:
await window.pwaTestSuite.runQuickTest()
```

### **Option 2: Comprehensive Testing (30 minutes)**

```bash
# Run full test suite
await window.pwaTestSuite.runAllTests()

# Test on multiple devices:
# - Open on iPhone Safari
# - Open on Android Chrome
# - Test installation on both
# - Test offline functionality
```

### **Option 3: Production Readiness (2 hours)**

```bash
# 1. Run Lighthouse audit
lighthouse https://your-domain.com --only-categories=pwa

# 2. Test real device installation
# 3. Test offline scenarios
# 4. Test performance under load
# 5. Validate across browser matrix
```

## 🚨 Critical Test Points

### **Must Pass Before Production:**

1. **PWA Score >90**: Lighthouse audit must pass
2. **Installation Works**: On both iOS and Android
3. **Offline Functional**: Core features work without network
4. **Performance Good**: <3s loading on slow connections
5. **No Console Errors**: Clean console logs

### **Red Flags to Fix:**

- Service Worker registration failures
- Manifest validation errors
- Cache strategy not working
- Camera/notifications completely broken
- Poor mobile responsiveness

---

**Ready to start testing?** Run this command in your browser console:

```javascript
// Start comprehensive PWA testing
await window.pwaTestSuite.runAllTests().then((results) => {
  console.log("🎉 PWA Testing Complete!");
  console.log("Results:", results);
  window.pwaTestSuite.displayTestReport();
});
```
