/**
 * Device Integration - PWA device API integration
 * Handles camera, notifications, storage, and other device capabilities
 */

class DeviceIntegration {
  constructor() {
    this.notificationPermission = "default";
    this.cameraStream = null;
    this.isSupported = {
      camera: this.checkCameraSupport(),
      notifications: this.checkNotificationSupport(),
      storage: this.checkStorageSupport(),
      geolocation: this.checkGeolocationSupport(),
      vibration: this.checkVibrationSupport(),
    };

    this.init();
  }

  async init() {
    // Check permissions
    await this.checkPermissions();

    // Set up notification handling
    this.setupNotifications();

    // Initialize storage
    this.initializeStorage();

    console.log("Device Integration initialized", this.isSupported);
  }

  // ============================================================================
  // CAMERA API INTEGRATION
  // ============================================================================

  checkCameraSupport() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  async requestCameraPermission() {
    if (!this.isSupported.camera) {
      throw new Error("Camera not supported on this device");
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment", // Use rear camera by default
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });

      console.log("Camera permission granted");
      return stream;
    } catch (error) {
      console.error("Camera permission denied:", error);
      throw error;
    }
  }

  async captureScreenshot() {
    try {
      const stream = await this.requestCameraPermission();

      // Create video element
      const video = document.createElement("video");
      video.srcObject = stream;
      video.autoplay = true;
      video.playsInline = true;

      return new Promise((resolve, reject) => {
        video.addEventListener("loadedmetadata", () => {
          // Create canvas for capture
          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");

          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;

          // Draw video frame to canvas
          context.drawImage(video, 0, 0);

          // Convert to blob
          canvas.toBlob(
            (blob) => {
              // Stop camera stream
              stream.getTracks().forEach((track) => track.stop());

              if (blob) {
                resolve(blob);
              } else {
                reject(new Error("Failed to capture screenshot"));
              }
            },
            "image/jpeg",
            0.9
          );
        });

        video.addEventListener("error", (error) => {
          stream.getTracks().forEach((track) => track.stop());
          reject(error);
        });
      });
    } catch (error) {
      console.error("Screenshot capture failed:", error);
      throw error;
    }
  }

  async openCameraModal() {
    return new Promise((resolve, reject) => {
      const modal = this.createCameraModal(resolve, reject);
      document.body.appendChild(modal);
    });
  }

  createCameraModal(resolve, reject) {
    const modal = document.createElement("div");
    modal.className = "camera-modal-overlay";
    modal.innerHTML = `
      <div class="camera-modal">
        <div class="camera-header">
          <h3>Capture MLBB Screenshot</h3>
          <button class="camera-close" onclick="this.closest('.camera-modal-overlay').remove(); arguments[1](new Error('Cancelled'));">×</button>
        </div>
        <div class="camera-content">
          <video id="camera-video" autoplay playsinline></video>
          <div class="camera-overlay">
            <div class="camera-guide">
              <p>📱 Position your MLBB game screen within the frame</p>
              <p>🎯 Ensure the scoreboard is clearly visible</p>
            </div>
          </div>
        </div>
        <div class="camera-actions">
          <button class="camera-capture-btn" onclick="window.deviceIntegration.handleCameraCapture(arguments[0], arguments[1])">
            📷 Capture Screenshot
          </button>
          <button class="camera-cancel-btn" onclick="this.closest('.camera-modal-overlay').remove(); arguments[1](new Error('Cancelled'));">
            Cancel
          </button>
        </div>
      </div>
    `;

    // Add camera modal styles
    this.addCameraModalStyles();

    // Initialize camera
    this.initializeCameraModal(modal, resolve, reject);

    return modal;
  }

  async initializeCameraModal(modal, resolve, reject) {
    try {
      const video = modal.querySelector("#camera-video");
      const stream = await this.requestCameraPermission();

      video.srcObject = stream;

      // Store references for capture
      modal.cameraStream = stream;
      modal.cameraVideo = video;
      modal.resolveCapture = resolve;
      modal.rejectCapture = reject;
    } catch (error) {
      modal.remove();
      reject(error);
    }
  }

  async handleCameraCapture(event, resolve, reject) {
    const modal = event.target.closest(".camera-modal-overlay");
    const video = modal.cameraVideo;
    const stream = modal.cameraStream;

    try {
      // Create canvas for capture
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw video frame
      context.drawImage(video, 0, 0);

      // Convert to blob
      canvas.toBlob(
        (blob) => {
          // Stop camera
          stream.getTracks().forEach((track) => track.stop());

          // Close modal
          modal.remove();

          if (blob) {
            modal.resolveCapture(blob);
          } else {
            modal.rejectCapture(new Error("Failed to capture"));
          }
        },
        "image/jpeg",
        0.9
      );
    } catch (error) {
      stream.getTracks().forEach((track) => track.stop());
      modal.remove();
      modal.rejectCapture(error);
    }
  }

  addCameraModalStyles() {
    if (document.getElementById("camera-modal-styles")) return;

    const style = document.createElement("style");
    style.id = "camera-modal-styles";
    style.textContent = `
      .camera-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.9);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .camera-modal {
        background: #1a1a2e;
        border-radius: 16px;
        width: 90%;
        max-width: 400px;
        max-height: 80vh;
        overflow: hidden;
      }
      
      .camera-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }
      
      .camera-header h3 {
        margin: 0;
        color: #ffffff;
      }
      
      .camera-close {
        background: none;
        border: none;
        color: #8892b0;
        font-size: 24px;
        cursor: pointer;
      }
      
      .camera-content {
        position: relative;
        padding: 20px;
      }
      
      #camera-video {
        width: 100%;
        border-radius: 12px;
        background: #000;
      }
      
      .camera-overlay {
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        bottom: 20px;
        pointer-events: none;
        display: flex;
        align-items: flex-end;
        justify-content: center;
      }
      
      .camera-guide {
        background: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-size: 12px;
        margin-bottom: 20px;
      }
      
      .camera-guide p {
        margin: 4px 0;
      }
      
      .camera-actions {
        display: flex;
        gap: 12px;
        padding: 20px;
      }
      
      .camera-capture-btn {
        flex: 1;
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
        color: white;
        border: none;
        padding: 16px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
      }
      
      .camera-cancel-btn {
        background: transparent;
        border: 2px solid #8892b0;
        color: #8892b0;
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 16px;
        cursor: pointer;
      }
    `;

    document.head.appendChild(style);
  }

  // ============================================================================
  // NOTIFICATION API INTEGRATION
  // ============================================================================

  checkNotificationSupport() {
    return "Notification" in window;
  }

  async checkPermissions() {
    if (this.isSupported.notifications) {
      this.notificationPermission = await Notification.requestPermission();
      console.log("Notification permission:", this.notificationPermission);
    }
  }

  async requestNotificationPermission() {
    if (!this.isSupported.notifications) {
      throw new Error("Notifications not supported");
    }

    const permission = await Notification.requestPermission();
    this.notificationPermission = permission;

    if (permission === "granted") {
      console.log("Notification permission granted");

      // Subscribe to push notifications
      await this.subscribeToPushNotifications();

      return true;
    } else {
      console.log("Notification permission denied");
      return false;
    }
  }

  async subscribeToPushNotifications() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      console.log("Push notifications not supported");
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.ready;

      // Check if already subscribed
      let subscription = await registration.pushManager.getSubscription();

      if (!subscription) {
        // Create new subscription
        const vapidPublicKey = "YOUR_VAPID_PUBLIC_KEY"; // Replace with actual VAPID key

        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey),
        });

        console.log("Push subscription created:", subscription);

        // Send subscription to server
        await this.sendSubscriptionToServer(subscription);
      }

      return subscription;
    } catch (error) {
      console.error("Push subscription failed:", error);
      return null;
    }
  }

  urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, "+")
      .replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  async sendSubscriptionToServer(subscription) {
    try {
      const response = await fetch("/api/push/subscribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          subscription: subscription,
          userAgent: navigator.userAgent,
        }),
      });

      if (response.ok) {
        console.log("Push subscription sent to server");
      } else {
        console.error("Failed to send subscription to server");
      }
    } catch (error) {
      console.error("Error sending subscription to server:", error);
    }
  }

  async showNotification(title, options = {}) {
    if (this.notificationPermission !== "granted") {
      console.log("Notification permission not granted");
      return;
    }

    const defaultOptions = {
      icon: "/images/icons/icon-192x192.png",
      badge: "/images/icons/badge-72x72.png",
      vibrate: [200, 100, 200],
      requireInteraction: false,
      silent: false,
    };

    const notificationOptions = { ...defaultOptions, ...options };

    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.showNotification(title, notificationOptions);
      console.log("Notification shown:", title);
    } catch (error) {
      console.error("Failed to show notification:", error);

      // Fallback to regular notification
      if (this.notificationPermission === "granted") {
        new Notification(title, notificationOptions);
      }
    }
  }

  setupNotifications() {
    if (!this.isSupported.notifications) return;

    // Handle notification click events
    navigator.serviceWorker.addEventListener("message", (event) => {
      if (event.data && event.data.type === "NOTIFICATION_CLICK") {
        this.handleNotificationClick(event.data);
      }
    });
  }

  handleNotificationClick(data) {
    console.log("Notification clicked:", data);

    // Navigate to relevant page based on notification type
    if (data.url) {
      window.location.href = data.url;
    }
  }

  // ============================================================================
  // STORAGE API INTEGRATION
  // ============================================================================

  checkStorageSupport() {
    return "localStorage" in window && "sessionStorage" in window;
  }

  async initializeStorage() {
    if (!this.isSupported.storage) return;

    // Check storage quota
    if ("storage" in navigator && "estimate" in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        console.log("Storage estimate:", {
          quota: this.formatBytes(estimate.quota),
          usage: this.formatBytes(estimate.usage),
          available: this.formatBytes(estimate.quota - estimate.usage),
        });

        // Request persistent storage
        if ("persist" in navigator.storage) {
          const persistent = await navigator.storage.persist();
          console.log("Persistent storage:", persistent);
        }
      } catch (error) {
        console.error("Storage API error:", error);
      }
    }
  }

  formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // Offline data storage
  async storeOfflineData(storeName, data) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open("MLBBCoachOffline", 1);

      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction([storeName], "readwrite");
        const store = transaction.objectStore(storeName);

        const addRequest = store.add({
          data: data,
          timestamp: new Date().toISOString(),
          synced: false,
        });

        addRequest.onsuccess = () => resolve(addRequest.result);
        addRequest.onerror = () => reject(addRequest.error);
      };

      request.onerror = () => reject(request.error);
    });
  }

  async getOfflineData(storeName) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open("MLBBCoachOffline", 1);

      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction([storeName], "readonly");
        const store = transaction.objectStore(storeName);
        const getAllRequest = store.getAll();

        getAllRequest.onsuccess = () => resolve(getAllRequest.result);
        getAllRequest.onerror = () => reject(getAllRequest.error);
      };

      request.onerror = () => reject(request.error);
    });
  }

  // ============================================================================
  // GEOLOCATION API (for regional features)
  // ============================================================================

  checkGeolocationSupport() {
    return "geolocation" in navigator;
  }

  async getCurrentLocation() {
    if (!this.isSupported.geolocation) {
      throw new Error("Geolocation not supported");
    }

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          });
        },
        (error) => {
          reject(error);
        },
        {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 300000, // 5 minutes
        }
      );
    });
  }

  // ============================================================================
  // VIBRATION API
  // ============================================================================

  checkVibrationSupport() {
    return "vibrate" in navigator;
  }

  vibrate(pattern = [200]) {
    if (this.isSupported.vibration) {
      navigator.vibrate(pattern);
    }
  }

  // Predefined vibration patterns
  vibrateSuccess() {
    this.vibrate([100, 50, 100]);
  }

  vibrateError() {
    this.vibrate([200, 100, 200, 100, 200]);
  }

  vibrateNotification() {
    this.vibrate([150]);
  }

  // ============================================================================
  // DEVICE ORIENTATION (for optimal viewing)
  // ============================================================================

  setupOrientationHandling() {
    if ("orientation" in screen) {
      screen.orientation.addEventListener("change", () => {
        console.log("Orientation changed:", screen.orientation.angle);
        this.handleOrientationChange();
      });
    }

    window.addEventListener("orientationchange", () => {
      this.handleOrientationChange();
    });
  }

  handleOrientationChange() {
    // Dispatch custom event for components to handle
    window.dispatchEvent(
      new CustomEvent("device-orientation-change", {
        detail: {
          angle: screen.orientation?.angle || window.orientation,
          type: screen.orientation?.type || "unknown",
        },
      })
    );
  }

  // ============================================================================
  // CLIPBOARD API (for sharing)
  // ============================================================================

  async copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        console.log("Text copied to clipboard");
        return true;
      } else {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const result = document.execCommand("copy");
        textArea.remove();

        return result;
      }
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
      return false;
    }
  }

  async readFromClipboard() {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        const text = await navigator.clipboard.readText();
        return text;
      } else {
        throw new Error("Clipboard read not supported");
      }
    } catch (error) {
      console.error("Failed to read from clipboard:", error);
      return null;
    }
  }

  // ============================================================================
  // SHARE API (for social sharing)
  // ============================================================================

  async shareContent(shareData) {
    try {
      if (navigator.share) {
        await navigator.share(shareData);
        console.log("Content shared successfully");
        return true;
      } else {
        // Fallback to clipboard copy
        const shareText = `${shareData.title}\n${shareData.text}\n${shareData.url}`;
        const copied = await this.copyToClipboard(shareText);

        if (copied) {
          this.showToast("Share link copied to clipboard!");
        }

        return copied;
      }
    } catch (error) {
      console.error("Share failed:", error);
      return false;
    }
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  showToast(message, type = "info", duration = 3000) {
    const toast = document.createElement("div");
    toast.className = `mobile-toast mobile-toast-${type}`;
    toast.textContent = message;

    // Add toast styles if not already added
    this.addToastStyles();

    document.body.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
      toast.remove();
    }, duration);
  }

  addToastStyles() {
    if (document.getElementById("toast-styles")) return;

    const style = document.createElement("style");
    style.id = "toast-styles";
    style.textContent = `
      .mobile-toast {
        position: fixed;
        bottom: 120px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        font-size: 14px;
        font-weight: 500;
        z-index: 10000;
        animation: toastSlideUp 0.3s ease-out;
        max-width: 90%;
        text-align: center;
      }
      
      .mobile-toast-success {
        background: rgba(46, 204, 113, 0.9);
      }
      
      .mobile-toast-error {
        background: rgba(231, 76, 60, 0.9);
      }
      
      .mobile-toast-warning {
        background: rgba(241, 196, 15, 0.9);
        color: #2c3e50;
      }
      
      @keyframes toastSlideUp {
        from {
          transform: translateX(-50%) translateY(50px);
          opacity: 0;
        }
        to {
          transform: translateX(-50%) translateY(0);
          opacity: 1;
        }
      }
    `;

    document.head.appendChild(style);
  }

  // Device capability checks
  getDeviceInfo() {
    return {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
      screen: {
        width: screen.width,
        height: screen.height,
        availWidth: screen.availWidth,
        availHeight: screen.availHeight,
        colorDepth: screen.colorDepth,
        pixelDepth: screen.pixelDepth,
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      capabilities: this.isSupported,
    };
  }

  // Performance monitoring
  measurePerformance(name, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();

    console.log(`Performance: ${name} took ${(end - start).toFixed(2)}ms`);

    // Track performance metric
    if (window.gtag) {
      window.gtag("event", "performance_measure", {
        event_category: "PWA",
        event_label: name,
        value: Math.round(end - start),
      });
    }

    return result;
  }

  // Check other device capabilities
  checkGeolocationSupport() {
    return "geolocation" in navigator;
  }

  checkVibrationSupport() {
    return "vibrate" in navigator;
  }

  // Public API for components
  getCapabilities() {
    return this.isSupported;
  }

  getNotificationPermission() {
    return this.notificationPermission;
  }
}

// Initialize Device Integration
window.deviceIntegration = new DeviceIntegration();

export default DeviceIntegration;
