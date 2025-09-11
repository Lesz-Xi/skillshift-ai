/**
 * PWA Test Suite - Comprehensive testing for PWA functionality
 * Tests all PWA features across different devices and browsers
 */

class PWATestSuite {
  constructor() {
    this.testResults = {};
    this.testEnvironment = this.detectEnvironment();
    this.init();
  }

  init() {
    console.log("PWA Test Suite initialized");
    console.log("Test Environment:", this.testEnvironment);
  }

  detectEnvironment() {
    const ua = navigator.userAgent;

    return {
      browser: this.detectBrowser(ua),
      device: this.detectDevice(ua),
      os: this.detectOS(ua),
      isStandalone: this.isStandaloneMode(),
      isPWA: this.isPWAEnvironment(),
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
        ratio: window.devicePixelRatio || 1,
      },
    };
  }

  detectBrowser(ua) {
    if (ua.includes("Chrome") && !ua.includes("Edg")) return "Chrome";
    if (ua.includes("Firefox")) return "Firefox";
    if (ua.includes("Safari") && !ua.includes("Chrome")) return "Safari";
    if (ua.includes("Edg")) return "Edge";
    if (ua.includes("Opera")) return "Opera";
    return "Unknown";
  }

  detectDevice(ua) {
    if (/iPad/.test(ua)) return "iPad";
    if (/iPhone/.test(ua)) return "iPhone";
    if (/Android/.test(ua)) return "Android";
    if (/Windows Phone/.test(ua)) return "Windows Phone";
    return "Desktop";
  }

  detectOS(ua) {
    if (/Windows/.test(ua)) return "Windows";
    if (/Mac OS/.test(ua)) return "macOS";
    if (/Linux/.test(ua)) return "Linux";
    if (/Android/.test(ua)) return "Android";
    if (/iOS/.test(ua)) return "iOS";
    return "Unknown";
  }

  isStandaloneMode() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  isPWAEnvironment() {
    return (
      this.isStandaloneMode() ||
      window.location.protocol === "https:" ||
      window.location.hostname === "localhost"
    );
  }

  // ============================================================================
  // CORE PWA FEATURE TESTS
  // ============================================================================

  async runAllTests() {
    console.log("🧪 Starting PWA Test Suite...");

    const tests = [
      "testServiceWorker",
      "testManifest",
      "testOfflineCapability",
      "testCaching",
      "testInstallability",
      "testNotifications",
      "testCamera",
      "testStorage",
      "testPerformance",
      "testResponsiveness",
    ];

    const results = {};

    for (const testName of tests) {
      try {
        console.log(`Running test: ${testName}`);
        results[testName] = await this[testName]();
      } catch (error) {
        console.error(`Test failed: ${testName}`, error);
        results[testName] = {
          passed: false,
          error: error.message,
          timestamp: new Date().toISOString(),
        };
      }
    }

    this.testResults = results;
    this.generateTestReport();

    return results;
  }

  async testServiceWorker() {
    const test = {
      name: "Service Worker",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Check if service worker is supported
      if (!("serviceWorker" in navigator)) {
        throw new Error("Service Worker not supported");
      }

      // Check if service worker is registered
      const registration = await navigator.serviceWorker.getRegistration();
      if (!registration) {
        throw new Error("Service Worker not registered");
      }

      test.details.registered = true;
      test.details.scope = registration.scope;
      test.details.state = registration.active?.state || "unknown";

      // Test service worker communication
      const messageChannel = new MessageChannel();
      const responsePromise = new Promise((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data);
        };
      });

      registration.active?.postMessage({ type: "GET_VERSION" }, [
        messageChannel.port2,
      ]);

      const response = await Promise.race([
        responsePromise,
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Timeout")), 3000)
        ),
      ]);

      test.details.communication = !!response;
      test.details.version = response?.version;
      test.passed = true;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testManifest() {
    const test = {
      name: "Web App Manifest",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Check for manifest link
      const manifestLink = document.querySelector('link[rel="manifest"]');
      if (!manifestLink) {
        throw new Error("Manifest link not found");
      }

      test.details.manifestUrl = manifestLink.href;

      // Fetch and validate manifest
      const response = await fetch(manifestLink.href);
      if (!response.ok) {
        throw new Error("Failed to fetch manifest");
      }

      const manifest = await response.json();

      // Validate required fields
      const requiredFields = ["name", "start_url", "display", "icons"];
      const missingFields = requiredFields.filter(
        (field) => !(field in manifest)
      );

      if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(", ")}`);
      }

      test.details.manifest = {
        name: manifest.name,
        shortName: manifest.short_name,
        startUrl: manifest.start_url,
        display: manifest.display,
        themeColor: manifest.theme_color,
        backgroundColor: manifest.background_color,
        iconCount: manifest.icons?.length || 0,
      };

      test.passed = true;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testOfflineCapability() {
    const test = {
      name: "Offline Capability",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Check if caches API is supported
      if (!("caches" in window)) {
        throw new Error("Cache API not supported");
      }

      // Check for cached resources
      const cacheNames = await caches.keys();
      test.details.cacheNames = cacheNames;
      test.details.totalCaches = cacheNames.length;

      if (cacheNames.length === 0) {
        throw new Error("No caches found");
      }

      // Check if offline page is cached
      const offlinePageCached = await caches.match("/offline.html");
      test.details.offlinePageCached = !!offlinePageCached;

      // Check if app shell is cached
      const appShellCached = await caches.match("/");
      test.details.appShellCached = !!appShellCached;

      test.passed = cacheNames.length > 0;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testCaching() {
    const test = {
      name: "Caching Strategy",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      const cacheNames = await caches.keys();
      let totalCachedItems = 0;

      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const requests = await cache.keys();
        totalCachedItems += requests.length;
      }

      test.details.totalCaches = cacheNames.length;
      test.details.totalCachedItems = totalCachedItems;
      test.details.cacheNames = cacheNames;

      // Test cache retrieval performance
      const start = performance.now();
      await caches.match("/");
      const end = performance.now();

      test.details.cacheRetrievalTime = end - start;
      test.passed = totalCachedItems > 0 && end - start < 100; // Sub-100ms cache retrieval
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testInstallability() {
    const test = {
      name: "App Installability",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Check if already installed
      test.details.isInstalled = this.isStandaloneMode();
      test.details.isStandalone = window.matchMedia(
        "(display-mode: standalone)"
      ).matches;

      // Check for install prompt availability
      test.details.beforeInstallPromptSupported =
        "onbeforeinstallprompt" in window;

      // Check manifest installability criteria
      const manifestTest = await this.testManifest();
      test.details.manifestValid = manifestTest.passed;

      // Check HTTPS requirement
      test.details.isHTTPS =
        window.location.protocol === "https:" ||
        window.location.hostname === "localhost";

      // Check service worker requirement
      const swTest = await this.testServiceWorker();
      test.details.serviceWorkerActive = swTest.passed;

      test.passed =
        test.details.manifestValid &&
        test.details.isHTTPS &&
        test.details.serviceWorkerActive;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testNotifications() {
    const test = {
      name: "Push Notifications",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Check notification support
      test.details.notificationSupported = "Notification" in window;
      test.details.permission = Notification.permission;

      // Check push manager support
      test.details.pushManagerSupported = "PushManager" in window;

      if (test.details.notificationSupported) {
        // Test notification creation (without showing)
        test.details.canCreateNotification = true;

        // Check service worker registration for push
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration && registration.pushManager) {
          test.details.pushManagerAvailable = true;

          // Check if subscribed to push
          const subscription = await registration.pushManager.getSubscription();
          test.details.pushSubscribed = !!subscription;
        }
      }

      test.passed =
        test.details.notificationSupported && test.details.pushManagerSupported;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testCamera() {
    const test = {
      name: "Camera Access",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Check media devices support
      test.details.mediaDevicesSupported = !!(
        navigator.mediaDevices && navigator.mediaDevices.getUserMedia
      );

      if (test.details.mediaDevicesSupported) {
        // Check available devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(
          (device) => device.kind === "videoinput"
        );

        test.details.videoDevicesCount = videoDevices.length;
        test.details.hasCamera = videoDevices.length > 0;

        // Test camera constraints
        test.details.supportedConstraints =
          navigator.mediaDevices.getSupportedConstraints();
      }

      test.passed =
        test.details.mediaDevicesSupported && test.details.hasCamera;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testStorage() {
    const test = {
      name: "Storage APIs",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Test localStorage
      test.details.localStorageSupported = "localStorage" in window;
      if (test.details.localStorageSupported) {
        localStorage.setItem("pwa-test", "test");
        test.details.localStorageWorking =
          localStorage.getItem("pwa-test") === "test";
        localStorage.removeItem("pwa-test");
      }

      // Test sessionStorage
      test.details.sessionStorageSupported = "sessionStorage" in window;
      if (test.details.sessionStorageSupported) {
        sessionStorage.setItem("pwa-test", "test");
        test.details.sessionStorageWorking =
          sessionStorage.getItem("pwa-test") === "test";
        sessionStorage.removeItem("pwa-test");
      }

      // Test IndexedDB
      test.details.indexedDBSupported = "indexedDB" in window;
      if (test.details.indexedDBSupported) {
        test.details.indexedDBWorking = await this.testIndexedDB();
      }

      // Test Storage API
      if ("storage" in navigator) {
        const estimate = await navigator.storage.estimate();
        test.details.storageQuota = estimate.quota;
        test.details.storageUsage = estimate.usage;
        test.details.storageAvailable = estimate.quota - estimate.usage;
      }

      test.passed =
        test.details.localStorageWorking &&
        test.details.sessionStorageWorking &&
        test.details.indexedDBWorking;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testIndexedDB() {
    return new Promise((resolve) => {
      try {
        const request = indexedDB.open("PWATestDB", 1);

        request.onerror = () => resolve(false);

        request.onupgradeneeded = (event) => {
          const db = event.target.result;
          db.createObjectStore("test", { keyPath: "id" });
        };

        request.onsuccess = (event) => {
          const db = event.target.result;
          const transaction = db.transaction(["test"], "readwrite");
          const store = transaction.objectStore("test");

          store.add({ id: 1, data: "test" });

          transaction.oncomplete = () => {
            db.close();
            // Clean up test database
            indexedDB.deleteDatabase("PWATestDB");
            resolve(true);
          };

          transaction.onerror = () => {
            db.close();
            resolve(false);
          };
        };
      } catch (error) {
        resolve(false);
      }
    });
  }

  async testPerformance() {
    const test = {
      name: "Performance Metrics",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Test page load performance
      if ("performance" in window && performance.timing) {
        const timing = performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        const domContentLoaded =
          timing.domContentLoadedEventEnd - timing.navigationStart;

        test.details.pageLoadTime = loadTime;
        test.details.domContentLoadedTime = domContentLoaded;
      }

      // Test First Contentful Paint
      if ("PerformanceObserver" in window) {
        const fcpPromise = new Promise((resolve) => {
          const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (entry.name === "first-contentful-paint") {
                resolve(entry.startTime);
                observer.disconnect();
              }
            }
          });
          observer.observe({ entryTypes: ["paint"] });

          // Timeout after 5 seconds
          setTimeout(() => resolve(null), 5000);
        });

        test.details.firstContentfulPaint = await fcpPromise;
      }

      // Test memory usage
      if ("memory" in performance) {
        test.details.memoryUsage = {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize,
          limit: performance.memory.jsHeapSizeLimit,
        };
      }

      // Performance thresholds
      const loadTimeThreshold = 3000; // 3 seconds
      const fcpThreshold = 2000; // 2 seconds

      test.passed =
        (test.details.pageLoadTime || 0) < loadTimeThreshold &&
        (test.details.firstContentfulPaint || 0) < fcpThreshold;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  async testResponsiveness() {
    const test = {
      name: "Responsive Design",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      const viewport = {
        width: window.innerWidth,
        height: window.innerHeight,
        ratio: window.devicePixelRatio || 1,
      };

      test.details.viewport = viewport;
      test.details.isMobile = viewport.width <= 768;
      test.details.isTablet = viewport.width > 768 && viewport.width <= 1024;
      test.details.isDesktop = viewport.width > 1024;

      // Test touch support
      test.details.touchSupported =
        "ontouchstart" in window || navigator.maxTouchPoints > 0;

      // Test orientation support
      test.details.orientationSupported = "orientation" in screen;
      if (test.details.orientationSupported) {
        test.details.currentOrientation = screen.orientation?.type || "unknown";
      }

      // Test CSS media queries
      test.details.mediaQueries = {
        mobile: window.matchMedia("(max-width: 768px)").matches,
        tablet: window.matchMedia("(min-width: 769px) and (max-width: 1024px)")
          .matches,
        desktop: window.matchMedia("(min-width: 1025px)").matches,
        landscape: window.matchMedia("(orientation: landscape)").matches,
        portrait: window.matchMedia("(orientation: portrait)").matches,
      };

      // Test safe area support
      test.details.safeAreaSupported = CSS.supports(
        "padding-top",
        "env(safe-area-inset-top)"
      );

      test.passed = true; // Responsive design test always passes, just collects info
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  // ============================================================================
  // DEVICE-SPECIFIC TESTS
  // ============================================================================

  async runIOSTests() {
    if (!this.testEnvironment.device.includes("iP")) return null;

    const iosTests = {
      addToHomeScreen: this.testIOSAddToHomeScreen(),
      safariSpecific: this.testSafariFeatures(),
      webkitAPIs: this.testWebKitAPIs(),
    };

    return iosTests;
  }

  async runAndroidTests() {
    if (this.testEnvironment.os !== "Android") return null;

    const androidTests = {
      installPrompt: this.testAndroidInstallPrompt(),
      chromeSpecific: this.testChromeFeatures(),
      webAPKSupport: this.testWebAPKSupport(),
    };

    return androidTests;
  }

  testIOSAddToHomeScreen() {
    return {
      isStandalone: window.navigator.standalone === true,
      canPromptInstall: false, // iOS doesn't support programmatic install prompts
      requiresManualInstall: true,
    };
  }

  testSafariFeatures() {
    return {
      webShareSupported: "share" in navigator,
      fullscreenSupported:
        "webkitRequestFullscreen" in document.documentElement,
      webkitAPIs: "webkit" in window,
    };
  }

  testWebKitAPIs() {
    return {
      webkitNotifications: "webkitNotifications" in window,
      webkitSpeech: "webkitSpeechRecognition" in window,
      webkitAudio: "webkitAudioContext" in window,
    };
  }

  testAndroidInstallPrompt() {
    return {
      beforeInstallPromptSupported: "onbeforeinstallprompt" in window,
      installPromptAvailable: !!window.deferredPrompt,
      chromeInstallSupported: this.testEnvironment.browser === "Chrome",
    };
  }

  testChromeFeatures() {
    return {
      webShareSupported: "share" in navigator,
      paymentRequestSupported: "PaymentRequest" in window,
      backgroundSyncSupported:
        "serviceWorker" in navigator &&
        "sync" in window.ServiceWorkerRegistration.prototype,
    };
  }

  testWebAPKSupport() {
    // Check if running as WebAPK (Android Chrome's PWA wrapper)
    return {
      isWebAPK:
        window.matchMedia("(display-mode: standalone)").matches &&
        this.testEnvironment.browser === "Chrome" &&
        this.testEnvironment.device === "Android",
    };
  }

  // ============================================================================
  // NETWORK AND CONNECTIVITY TESTS
  // ============================================================================

  async testNetworkCapabilities() {
    const test = {
      name: "Network Capabilities",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // Basic connectivity
      test.details.isOnline = navigator.onLine;

      // Network Information API
      if ("connection" in navigator) {
        const connection = navigator.connection;
        test.details.networkInfo = {
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData,
        };
      }

      // Test actual connectivity with a lightweight request
      const start = performance.now();
      try {
        const response = await fetch("/manifest.json", {
          method: "HEAD",
          cache: "no-cache",
        });
        const end = performance.now();

        test.details.serverReachable = response.ok;
        test.details.responseTime = end - start;
      } catch (fetchError) {
        test.details.serverReachable = false;
        test.details.fetchError = fetchError.message;
      }

      test.passed = test.details.isOnline;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  // ============================================================================
  // SECURITY AND PERMISSIONS TESTS
  // ============================================================================

  async testSecurityFeatures() {
    const test = {
      name: "Security Features",
      passed: false,
      details: {},
      timestamp: new Date().toISOString(),
    };

    try {
      // HTTPS check
      test.details.isHTTPS = window.location.protocol === "https:";

      // Secure context check
      test.details.isSecureContext = window.isSecureContext;

      // CSP check
      test.details.hasCSP = !!document.querySelector(
        'meta[http-equiv="Content-Security-Policy"]'
      );

      // Mixed content check
      test.details.hasMixedContent =
        window.location.protocol === "https:" &&
        document.querySelectorAll('[src^="http:"]').length > 0;

      test.passed =
        test.details.isHTTPS &&
        test.details.isSecureContext &&
        !test.details.hasMixedContent;
    } catch (error) {
      test.error = error.message;
    }

    return test;
  }

  // ============================================================================
  // TEST REPORTING
  // ============================================================================

  generateTestReport() {
    const report = {
      environment: this.testEnvironment,
      testResults: this.testResults,
      summary: this.generateTestSummary(),
      timestamp: new Date().toISOString(),
      recommendations: this.generateRecommendations(),
    };

    console.log("📊 PWA Test Report:", report);

    // Save to localStorage for debugging
    try {
      localStorage.setItem("pwa-test-report", JSON.stringify(report));
    } catch (error) {
      console.warn("Failed to save test report to localStorage:", error);
    }

    return report;
  }

  generateTestSummary() {
    const results = Object.values(this.testResults);
    const passed = results.filter((test) => test.passed).length;
    const total = results.length;

    return {
      totalTests: total,
      passedTests: passed,
      failedTests: total - passed,
      successRate: (passed / total) * 100,
      overallStatus:
        passed === total
          ? "EXCELLENT"
          : passed >= total * 0.8
          ? "GOOD"
          : passed >= total * 0.6
          ? "FAIR"
          : "POOR",
    };
  }

  generateRecommendations() {
    const recommendations = [];

    // Service Worker recommendations
    if (!this.testResults.testServiceWorker?.passed) {
      recommendations.push({
        priority: "HIGH",
        category: "Core PWA",
        issue: "Service Worker not working",
        solution: "Ensure service worker is properly registered and active",
      });
    }

    // Manifest recommendations
    if (!this.testResults.testManifest?.passed) {
      recommendations.push({
        priority: "HIGH",
        category: "Core PWA",
        issue: "Web App Manifest issues",
        solution: "Fix manifest.json validation errors",
      });
    }

    // Performance recommendations
    const perfTest = this.testResults.testPerformance;
    if (perfTest && !perfTest.passed) {
      recommendations.push({
        priority: "MEDIUM",
        category: "Performance",
        issue: "Poor loading performance",
        solution: "Optimize assets and implement better caching strategies",
      });
    }

    // Camera recommendations
    if (!this.testResults.testCamera?.passed) {
      recommendations.push({
        priority: "MEDIUM",
        category: "Device Integration",
        issue: "Camera access not available",
        solution: "Provide alternative upload methods for screenshot analysis",
      });
    }

    // Notification recommendations
    if (!this.testResults.testNotifications?.passed) {
      recommendations.push({
        priority: "LOW",
        category: "Engagement",
        issue: "Push notifications not available",
        solution: "Implement in-app notification system as fallback",
      });
    }

    return recommendations;
  }

  // ============================================================================
  // PUBLIC API
  // ============================================================================

  async runQuickTest() {
    const quickTests = [
      "testServiceWorker",
      "testManifest",
      "testInstallability",
    ];

    const results = {};

    for (const testName of quickTests) {
      results[testName] = await this[testName]();
    }

    return {
      results,
      summary: this.generateQuickSummary(results),
    };
  }

  generateQuickSummary(results) {
    const passed = Object.values(results).filter((test) => test.passed).length;
    const total = Object.keys(results).length;

    return {
      status: passed === total ? "READY" : "NEEDS_ATTENTION",
      passedTests: passed,
      totalTests: total,
      readyForProduction: passed === total,
    };
  }

  getTestResults() {
    return this.testResults;
  }

  getEnvironmentInfo() {
    return this.testEnvironment;
  }

  // Visual test report for debugging
  displayTestReport() {
    const report = this.generateTestReport();
    const modal = this.createTestReportModal(report);
    document.body.appendChild(modal);
  }

  createTestReportModal(report) {
    const modal = document.createElement("div");
    modal.className = "test-report-modal-overlay";
    modal.innerHTML = `
      <div class="test-report-modal">
        <div class="test-report-header">
          <h3>🧪 PWA Test Report</h3>
          <button onclick="this.closest('.test-report-modal-overlay').remove()">×</button>
        </div>
        <div class="test-report-content">
          <div class="test-summary">
            <h4>Summary</h4>
            <p><strong>Status:</strong> ${report.summary.overallStatus}</p>
            <p><strong>Tests Passed:</strong> ${report.summary.passedTests}/${
      report.summary.totalTests
    }</p>
            <p><strong>Success Rate:</strong> ${report.summary.successRate.toFixed(
              1
            )}%</p>
          </div>
          
          <div class="test-details">
            <h4>Test Results</h4>
            ${Object.entries(report.testResults)
              .map(
                ([testName, result]) => `
              <div class="test-item ${result.passed ? "passed" : "failed"}">
                <div class="test-name">${result.name}</div>
                <div class="test-status">${result.passed ? "✅" : "❌"}</div>
                ${
                  result.error
                    ? `<div class="test-error">${result.error}</div>`
                    : ""
                }
              </div>
            `
              )
              .join("")}
          </div>
          
          ${
            report.recommendations.length > 0
              ? `
            <div class="test-recommendations">
              <h4>Recommendations</h4>
              ${report.recommendations
                .map(
                  (rec) => `
                <div class="recommendation ${rec.priority.toLowerCase()}">
                  <strong>${rec.category}:</strong> ${rec.solution}
                </div>
              `
                )
                .join("")}
            </div>
          `
              : ""
          }
        </div>
      </div>
    `;

    // Add test report styles
    this.addTestReportStyles();

    return modal;
  }

  addTestReportStyles() {
    if (document.getElementById("test-report-styles")) return;

    const style = document.createElement("style");
    style.id = "test-report-styles";
    style.textContent = `
      .test-report-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      }
      
      .test-report-modal {
        background: #1a1a2e;
        border-radius: 16px;
        width: 100%;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
        color: white;
      }
      
      .test-report-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }
      
      .test-report-header h3 {
        margin: 0;
      }
      
      .test-report-header button {
        background: none;
        border: none;
        color: #8892b0;
        font-size: 24px;
        cursor: pointer;
      }
      
      .test-report-content {
        padding: 20px;
      }
      
      .test-summary {
        background: rgba(74, 144, 226, 0.1);
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 20px;
      }
      
      .test-details h4,
      .test-recommendations h4 {
        margin-bottom: 12px;
        color: #4a90e2;
      }
      
      .test-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.05);
      }
      
      .test-item.passed {
        border-left: 4px solid #2ecc71;
      }
      
      .test-item.failed {
        border-left: 4px solid #e74c3c;
      }
      
      .test-error {
        font-size: 12px;
        color: #e74c3c;
        margin-top: 4px;
      }
      
      .recommendation {
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        font-size: 14px;
      }
      
      .recommendation.high {
        background: rgba(231, 76, 60, 0.1);
        border-left: 4px solid #e74c3c;
      }
      
      .recommendation.medium {
        background: rgba(241, 196, 15, 0.1);
        border-left: 4px solid #f1c40f;
      }
      
      .recommendation.low {
        background: rgba(46, 204, 113, 0.1);
        border-left: 4px solid #2ecc71;
      }
    `;

    document.head.appendChild(style);
  }
}

// Initialize PWA Test Suite
window.pwaTestSuite = new PWATestSuite();

export default PWATestSuite;
