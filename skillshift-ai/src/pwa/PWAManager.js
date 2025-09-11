/**
 * PWA Manager - Handles PWA functionality and service worker communication
 */

class PWAManager {
  constructor() {
    this.swRegistration = null;
    this.isOnline = navigator.onLine;
    this.updateAvailable = false;
    this.deferredPrompt = null;
    this.installPromptShown = false;

    this.init();
  }

  async init() {
    // Register service worker
    await this.registerServiceWorker();

    // Set up event listeners
    this.setupEventListeners();

    // Check for updates
    this.checkForUpdates();

    // Handle install prompt
    this.setupInstallPrompt();

    // Initialize offline support
    this.initializeOfflineSupport();

    console.log("PWA Manager initialized");
  }

  async registerServiceWorker() {
    if ("serviceWorker" in navigator) {
      try {
        const registration = await navigator.serviceWorker.register("/sw.js", {
          scope: "/",
        });

        this.swRegistration = registration;
        console.log("Service Worker registered successfully:", registration);

        // Listen for updates
        registration.addEventListener("updatefound", () => {
          const newWorker = registration.installing;

          newWorker.addEventListener("statechange", () => {
            if (
              newWorker.state === "installed" &&
              navigator.serviceWorker.controller
            ) {
              // New content is available
              this.updateAvailable = true;
              this.showUpdateNotification();
            }
          });
        });

        return registration;
      } catch (error) {
        console.error("Service Worker registration failed:", error);
        return null;
      }
    } else {
      console.log("Service Worker not supported");
      return null;
    }
  }

  setupEventListeners() {
    // Online/offline status
    window.addEventListener("online", () => {
      this.isOnline = true;
      this.handleOnlineStatus();
    });

    window.addEventListener("offline", () => {
      this.isOnline = false;
      this.handleOfflineStatus();
    });

    // App install prompt
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallPrompt();
    });

    // App installed
    window.addEventListener("appinstalled", () => {
      console.log("PWA was installed");
      this.deferredPrompt = null;
      this.hideInstallPrompt();

      // Track installation
      this.trackEvent("pwa_installed");
    });

    // Service worker messages
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.addEventListener("message", (event) => {
        this.handleServiceWorkerMessage(event.data);
      });
    }
  }

  checkForUpdates() {
    if (this.swRegistration) {
      // Check for updates every 30 minutes
      setInterval(() => {
        this.swRegistration.update();
      }, 30 * 60 * 1000);
    }
  }

  setupInstallPrompt() {
    // Check if already installed
    if (window.matchMedia("(display-mode: standalone)").matches) {
      console.log("App is running in standalone mode");
      return;
    }

    // Check if iOS Safari
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isInStandaloneMode = window.navigator.standalone;

    if (isIOS && !isInStandaloneMode) {
      this.showIOSInstallInstructions();
    }
  }

  initializeOfflineSupport() {
    // Initialize IndexedDB for offline data
    this.initializeOfflineDB();

    // Preload critical resources
    this.preloadCriticalResources();

    // Set up background sync
    this.setupBackgroundSync();
  }

  // PWA Installation
  async showInstallPrompt() {
    if (this.installPromptShown || !this.deferredPrompt) return;

    const installBanner = this.createInstallBanner();
    document.body.appendChild(installBanner);

    this.installPromptShown = true;

    // Auto-hide after 10 seconds
    setTimeout(() => {
      this.hideInstallPrompt();
    }, 10000);
  }

  createInstallBanner() {
    const banner = document.createElement("div");
    banner.id = "pwa-install-banner";
    banner.className = "pwa-install-banner";
    banner.innerHTML = `
      <div class="pwa-install-content">
        <div class="pwa-install-icon">🏆</div>
        <div class="pwa-install-text">
          <div class="pwa-install-title">Install MLBB Coach AI</div>
          <div class="pwa-install-subtitle">Get the full app experience with offline access</div>
        </div>
        <div class="pwa-install-actions">
          <button class="pwa-install-btn" onclick="window.pwaManager.installApp()">Install</button>
          <button class="pwa-install-close" onclick="window.pwaManager.hideInstallPrompt()">×</button>
        </div>
      </div>
    `;

    // Add styles
    const style = document.createElement("style");
    style.textContent = `
      .pwa-install-banner {
        position: fixed;
        bottom: 20px;
        left: 20px;
        right: 20px;
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
        color: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(74, 144, 226, 0.3);
        z-index: 10000;
        animation: slideUp 0.3s ease-out;
      }
      
      .pwa-install-content {
        display: flex;
        align-items: center;
        padding: 16px;
        gap: 12px;
      }
      
      .pwa-install-icon {
        font-size: 32px;
        flex-shrink: 0;
      }
      
      .pwa-install-text {
        flex: 1;
      }
      
      .pwa-install-title {
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 4px;
      }
      
      .pwa-install-subtitle {
        font-size: 14px;
        opacity: 0.9;
      }
      
      .pwa-install-actions {
        display: flex;
        gap: 8px;
        align-items: center;
      }
      
      .pwa-install-btn {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      
      .pwa-install-btn:hover {
        background: rgba(255, 255, 255, 0.3);
      }
      
      .pwa-install-close {
        background: none;
        color: white;
        border: none;
        font-size: 24px;
        cursor: pointer;
        padding: 4px;
        opacity: 0.7;
      }
      
      .pwa-install-close:hover {
        opacity: 1;
      }
      
      @keyframes slideUp {
        from {
          transform: translateY(100%);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }
      
      @media (max-width: 480px) {
        .pwa-install-banner {
          left: 10px;
          right: 10px;
          bottom: 10px;
        }
        
        .pwa-install-content {
          padding: 12px;
        }
        
        .pwa-install-title {
          font-size: 14px;
        }
        
        .pwa-install-subtitle {
          font-size: 12px;
        }
      }
    `;

    document.head.appendChild(style);

    return banner;
  }

  async installApp() {
    if (!this.deferredPrompt) return;

    try {
      // Show the install prompt
      this.deferredPrompt.prompt();

      // Wait for user response
      const { outcome } = await this.deferredPrompt.userChoice;

      console.log(`User response to install prompt: ${outcome}`);

      // Track the result
      this.trackEvent("pwa_install_prompt", { outcome });

      // Clear the prompt
      this.deferredPrompt = null;
      this.hideInstallPrompt();
    } catch (error) {
      console.error("Install prompt failed:", error);
    }
  }

  hideInstallPrompt() {
    const banner = document.getElementById("pwa-install-banner");
    if (banner) {
      banner.remove();
    }
    this.installPromptShown = false;
  }

  showIOSInstallInstructions() {
    // Show iOS-specific install instructions
    const instructions = this.createIOSInstructions();
    document.body.appendChild(instructions);
  }

  createIOSInstructions() {
    const modal = document.createElement("div");
    modal.id = "ios-install-modal";
    modal.innerHTML = `
      <div class="ios-install-overlay">
        <div class="ios-install-modal">
          <div class="ios-install-header">
            <h3>Install MLBB Coach AI</h3>
            <button onclick="this.closest('.ios-install-overlay').remove()">×</button>
          </div>
          <div class="ios-install-content">
            <p>To install this app on your iPhone/iPad:</p>
            <ol>
              <li>Tap the <strong>Share</strong> button <span class="ios-icon">⎙</span></li>
              <li>Scroll down and tap <strong>"Add to Home Screen"</strong> <span class="ios-icon">⊞</span></li>
              <li>Tap <strong>"Add"</strong> to confirm</li>
            </ol>
          </div>
        </div>
      </div>
    `;

    // Add iOS-specific styles
    const style = document.createElement("style");
    style.textContent = `
      .ios-install-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10001;
      }
      
      .ios-install-modal {
        background: white;
        border-radius: 12px;
        max-width: 300px;
        margin: 20px;
      }
      
      .ios-install-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 20px 0;
      }
      
      .ios-install-header h3 {
        margin: 0;
        color: #333;
      }
      
      .ios-install-header button {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
      }
      
      .ios-install-content {
        padding: 20px;
        color: #333;
      }
      
      .ios-install-content ol {
        margin: 16px 0;
        padding-left: 20px;
      }
      
      .ios-install-content li {
        margin: 12px 0;
        line-height: 1.4;
      }
      
      .ios-icon {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 18px;
        color: #007AFF;
      }
    `;

    document.head.appendChild(style);

    return modal;
  }

  // Update Management
  showUpdateNotification() {
    const notification = this.createUpdateNotification();
    document.body.appendChild(notification);
  }

  createUpdateNotification() {
    const notification = document.createElement("div");
    notification.id = "pwa-update-notification";
    notification.className = "pwa-update-notification";
    notification.innerHTML = `
      <div class="pwa-update-content">
        <div class="pwa-update-text">
          <strong>New version available!</strong>
          <p>Refresh to get the latest features and improvements.</p>
        </div>
        <div class="pwa-update-actions">
          <button class="pwa-update-btn" onclick="window.pwaManager.applyUpdate()">Update</button>
          <button class="pwa-update-dismiss" onclick="window.pwaManager.dismissUpdate()">Later</button>
        </div>
      </div>
    `;

    return notification;
  }

  async applyUpdate() {
    if (this.swRegistration && this.swRegistration.waiting) {
      // Tell the waiting SW to skip waiting
      this.swRegistration.waiting.postMessage({ type: "SKIP_WAITING" });

      // Reload the page
      window.location.reload();
    }
  }

  dismissUpdate() {
    const notification = document.getElementById("pwa-update-notification");
    if (notification) {
      notification.remove();
    }
  }

  // Offline Support
  async initializeOfflineDB() {
    try {
      const request = indexedDB.open("MLBBCoachOffline", 1);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create object stores for offline data
        if (!db.objectStoreNames.contains("analyses")) {
          db.createObjectStore("analyses", {
            keyPath: "id",
            autoIncrement: true,
          });
        }

        if (!db.objectStoreNames.contains("achievements")) {
          db.createObjectStore("achievements", {
            keyPath: "id",
            autoIncrement: true,
          });
        }

        if (!db.objectStoreNames.contains("learning")) {
          db.createObjectStore("learning", {
            keyPath: "id",
            autoIncrement: true,
          });
        }
      };

      request.onsuccess = () => {
        console.log("Offline database initialized");
      };

      request.onerror = (error) => {
        console.error("Failed to initialize offline database:", error);
      };
    } catch (error) {
      console.error("IndexedDB not supported:", error);
    }
  }

  async preloadCriticalResources() {
    const criticalResources = [
      "/static/css/main.css",
      "/static/js/main.js",
      "/images/icons/icon-192x192.png",
    ];

    if (this.swRegistration) {
      this.swRegistration.active?.postMessage({
        type: "CACHE_URLS",
        urls: criticalResources,
      });
    }
  }

  setupBackgroundSync() {
    if (
      "serviceWorker" in navigator &&
      "sync" in window.ServiceWorkerRegistration.prototype
    ) {
      console.log("Background sync supported");

      // Register sync events when needed
      this.registerBackgroundSync("background-sync-analysis");
      this.registerBackgroundSync("background-sync-achievements");
      this.registerBackgroundSync("background-sync-progress");
    }
  }

  async registerBackgroundSync(tag) {
    if (this.swRegistration) {
      try {
        await this.swRegistration.sync.register(tag);
        console.log(`Background sync registered: ${tag}`);
      } catch (error) {
        console.error(`Background sync registration failed: ${tag}`, error);
      }
    }
  }

  // Network Status Handling
  handleOnlineStatus() {
    console.log("App is online");

    // Show online indicator
    this.showConnectionStatus("online");

    // Trigger background sync
    this.registerBackgroundSync("background-sync-analysis");
    this.registerBackgroundSync("background-sync-achievements");
    this.registerBackgroundSync("background-sync-progress");

    // Dispatch custom event
    window.dispatchEvent(new CustomEvent("pwa-online"));
  }

  handleOfflineStatus() {
    console.log("App is offline");

    // Show offline indicator
    this.showConnectionStatus("offline");

    // Dispatch custom event
    window.dispatchEvent(new CustomEvent("pwa-offline"));
  }

  showConnectionStatus(status) {
    // Remove existing status
    const existing = document.getElementById("pwa-connection-status");
    if (existing) existing.remove();

    const statusBar = document.createElement("div");
    statusBar.id = "pwa-connection-status";
    statusBar.className = `pwa-connection-status ${status}`;
    statusBar.innerHTML =
      status === "online"
        ? "🌐 Back online"
        : "📡 You're offline - some features may be limited";

    document.body.appendChild(statusBar);

    // Auto-hide after 3 seconds
    setTimeout(() => {
      statusBar.remove();
    }, 3000);
  }

  // Service Worker Communication
  handleServiceWorkerMessage(data) {
    console.log("Message from Service Worker:", data);

    switch (data.type) {
      case "VERSION":
        console.log("Service Worker version:", data.version);
        break;

      case "CACHE_UPDATED":
        console.log("Cache updated:", data.cacheName);
        break;

      case "SYNC_COMPLETE":
        console.log("Background sync complete:", data.tag);
        this.showSyncNotification(data.tag);
        break;
    }
  }

  showSyncNotification(tag) {
    const messages = {
      "background-sync-analysis": "Analysis synced successfully",
      "background-sync-achievements": "Achievement progress synced",
      "background-sync-progress": "Learning progress synced",
    };

    const message = messages[tag] || "Data synced successfully";

    // Show brief notification
    const notification = document.createElement("div");
    notification.className = "pwa-sync-notification";
    notification.textContent = `✓ ${message}`;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 2000);
  }

  // Utility Methods
  trackEvent(eventName, properties = {}) {
    // Track PWA events for analytics
    if (window.gtag) {
      window.gtag("event", eventName, properties);
    }

    console.log("PWA Event:", eventName, properties);
  }

  // Public API
  isInstalled() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  getInstallPrompt() {
    return this.deferredPrompt;
  }

  isUpdateAvailable() {
    return this.updateAvailable;
  }

  getConnectionStatus() {
    return this.isOnline;
  }
}

// Initialize PWA Manager
window.pwaManager = new PWAManager();

export default PWAManager;
