#!/usr/bin/env node
/**
 * PWA Testing Script - Automated testing for MLBB Coach AI PWA
 * Run this script to validate PWA functionality
 */

const lighthouse = require("lighthouse");
const chromeLauncher = require("chrome-launcher");
const fs = require("fs");
const path = require("path");

class PWATester {
  constructor() {
    this.testResults = {};
    this.serverUrl = "http://localhost:3000"; // Adjust for your dev server
  }

  async runFullPWATest() {
    console.log("🧪 Starting comprehensive PWA testing...\n");

    try {
      // Test 1: Lighthouse PWA Audit
      console.log("📊 Running Lighthouse PWA audit...");
      const lighthouseResults = await this.runLighthouseAudit();
      this.testResults.lighthouse = lighthouseResults;

      // Test 2: Manifest Validation
      console.log("📋 Validating Web App Manifest...");
      const manifestResults = await this.validateManifest();
      this.testResults.manifest = manifestResults;

      // Test 3: Service Worker Testing
      console.log("⚙️ Testing Service Worker...");
      const swResults = await this.testServiceWorker();
      this.testResults.serviceWorker = swResults;

      // Test 4: Offline Capability
      console.log("📡 Testing offline capabilities...");
      const offlineResults = await this.testOfflineCapability();
      this.testResults.offline = offlineResults;

      // Generate comprehensive report
      const report = this.generateTestReport();

      console.log("\n🎉 PWA Testing Complete!");
      console.log("📊 Test Report Generated: pwa-test-report.json");

      return report;
    } catch (error) {
      console.error("❌ PWA testing failed:", error);
      return null;
    }
  }

  async runLighthouseAudit() {
    try {
      const chrome = await chromeLauncher.launch({
        chromeFlags: ["--headless", "--disable-gpu", "--no-sandbox"],
      });

      const options = {
        logLevel: "info",
        output: "json",
        onlyCategories: ["pwa"],
        port: chrome.port,
      };

      const runnerResult = await lighthouse(this.serverUrl, options);
      await chrome.kill();

      const pwaScore = runnerResult.lhr.categories.pwa.score * 100;
      const audits = runnerResult.lhr.audits;

      const results = {
        score: pwaScore,
        passed: pwaScore >= 90,
        details: {
          installable: audits["installable-manifest"]?.score === 1,
          serviceWorker: audits["service-worker"]?.score === 1,
          offlineSupport: audits["works-offline"]?.score === 1,
          httpsRedirect: audits["redirects-http"]?.score === 1,
          manifest: audits["manifest-short-name-length"]?.score === 1,
        },
        recommendations: this.extractLighthouseRecommendations(audits),
      };

      console.log(
        `   PWA Score: ${pwaScore}/100 ${pwaScore >= 90 ? "✅" : "❌"}`
      );

      return results;
    } catch (error) {
      console.error("   Lighthouse audit failed:", error.message);
      return { score: 0, passed: false, error: error.message };
    }
  }

  async validateManifest() {
    try {
      const manifestPath = path.join(__dirname, "public", "manifest.json");

      if (!fs.existsSync(manifestPath)) {
        throw new Error("Manifest file not found");
      }

      const manifestContent = fs.readFileSync(manifestPath, "utf8");
      const manifest = JSON.parse(manifestContent);

      const requiredFields = [
        "name",
        "short_name",
        "start_url",
        "display",
        "icons",
      ];
      const missingFields = requiredFields.filter((field) => !manifest[field]);

      const results = {
        exists: true,
        valid: missingFields.length === 0,
        missingFields,
        iconCount: manifest.icons ? manifest.icons.length : 0,
        hasShortcuts: !!manifest.shortcuts,
        details: {
          name: manifest.name,
          shortName: manifest.short_name,
          startUrl: manifest.start_url,
          display: manifest.display,
          themeColor: manifest.theme_color,
        },
      };

      console.log(`   Manifest valid: ${results.valid ? "✅" : "❌"}`);
      console.log(
        `   Icons: ${results.iconCount}, Shortcuts: ${
          manifest.shortcuts?.length || 0
        }`
      );

      return results;
    } catch (error) {
      console.error("   Manifest validation failed:", error.message);
      return { exists: false, valid: false, error: error.message };
    }
  }

  async testServiceWorker() {
    try {
      const swPath = path.join(__dirname, "public", "sw.js");

      if (!fs.existsSync(swPath)) {
        throw new Error("Service Worker file not found");
      }

      const swContent = fs.readFileSync(swPath, "utf8");

      const results = {
        exists: true,
        size: swContent.length,
        hasCaching: swContent.includes("caches.open"),
        hasOfflineSupport: swContent.includes("offline"),
        hasBackgroundSync: swContent.includes("sync"),
        hasPushHandling: swContent.includes("push"),
        features: {
          install: swContent.includes("install"),
          activate: swContent.includes("activate"),
          fetch: swContent.includes("fetch"),
          message: swContent.includes("message"),
        },
      };

      console.log(`   Service Worker: ${results.exists ? "✅" : "❌"}`);
      console.log(
        `   Features: Caching ${results.hasCaching ? "✅" : "❌"}, Offline ${
          results.hasOfflineSupport ? "✅" : "❌"
        }, Sync ${results.hasBackgroundSync ? "✅" : "❌"}`
      );

      return results;
    } catch (error) {
      console.error("   Service Worker test failed:", error.message);
      return { exists: false, error: error.message };
    }
  }

  async testOfflineCapability() {
    try {
      const offlinePath = path.join(__dirname, "public", "offline.html");

      const results = {
        offlinePageExists: fs.existsSync(offlinePath),
        offlinePageSize: 0,
        hasOfflineFeatures: false,
      };

      if (results.offlinePageExists) {
        const offlineContent = fs.readFileSync(offlinePath, "utf8");
        results.offlinePageSize = offlineContent.length;
        results.hasOfflineFeatures =
          offlineContent.includes("offline") &&
          offlineContent.includes("features");
      }

      console.log(
        `   Offline page: ${results.offlinePageExists ? "✅" : "❌"}`
      );
      console.log(
        `   Offline features: ${results.hasOfflineFeatures ? "✅" : "❌"}`
      );

      return results;
    } catch (error) {
      console.error("   Offline test failed:", error.message);
      return { error: error.message };
    }
  }

  extractLighthouseRecommendations(audits) {
    const recommendations = [];

    Object.entries(audits).forEach(([auditId, audit]) => {
      if (audit.score !== null && audit.score < 1) {
        recommendations.push({
          id: auditId,
          title: audit.title,
          description: audit.description,
          score: audit.score,
        });
      }
    });

    return recommendations;
  }

  generateTestReport() {
    const summary = this.calculateSummary();

    const report = {
      timestamp: new Date().toISOString(),
      summary,
      testResults: this.testResults,
      recommendations: this.generateRecommendations(),
      nextSteps: this.generateNextSteps(),
    };

    // Save to file
    fs.writeFileSync(
      path.join(__dirname, "pwa-test-report.json"),
      JSON.stringify(report, null, 2)
    );

    // Print summary
    this.printSummary(summary);

    return report;
  }

  calculateSummary() {
    const lighthouse = this.testResults.lighthouse;
    const manifest = this.testResults.manifest;
    const serviceWorker = this.testResults.serviceWorker;
    const offline = this.testResults.offline;

    const overallScore =
      (lighthouse?.score || 0) * 0.4 +
      (manifest?.valid ? 100 : 0) * 0.3 +
      (serviceWorker?.exists ? 100 : 0) * 0.2 +
      (offline?.offlinePageExists ? 100 : 0) * 0.1;

    return {
      overallScore: Math.round(overallScore),
      status:
        overallScore >= 90
          ? "EXCELLENT"
          : overallScore >= 75
          ? "GOOD"
          : overallScore >= 60
          ? "FAIR"
          : "POOR",
      readyForProduction: overallScore >= 90,
      criticalIssues: this.findCriticalIssues(),
      passedTests: this.countPassedTests(),
      totalTests: 4,
    };
  }

  findCriticalIssues() {
    const issues = [];

    if (!this.testResults.lighthouse?.passed) {
      issues.push("Lighthouse PWA audit failed");
    }

    if (!this.testResults.manifest?.valid) {
      issues.push("Web App Manifest invalid");
    }

    if (!this.testResults.serviceWorker?.exists) {
      issues.push("Service Worker missing or broken");
    }

    return issues;
  }

  countPassedTests() {
    return Object.values(this.testResults).filter(
      (result) => result.passed || result.valid || result.exists
    ).length;
  }

  generateRecommendations() {
    const recommendations = [];

    if (this.testResults.lighthouse?.score < 90) {
      recommendations.push({
        priority: "HIGH",
        category: "Performance",
        issue: "Lighthouse PWA score below 90",
        action: "Review Lighthouse recommendations and optimize",
      });
    }

    if (!this.testResults.manifest?.valid) {
      recommendations.push({
        priority: "HIGH",
        category: "Core PWA",
        issue: "Manifest validation failed",
        action:
          "Fix missing manifest fields: " +
          (this.testResults.manifest?.missingFields || []).join(", "),
      });
    }

    if (!this.testResults.serviceWorker?.hasCaching) {
      recommendations.push({
        priority: "MEDIUM",
        category: "Offline",
        issue: "Service Worker lacks caching",
        action: "Implement proper caching strategies",
      });
    }

    return recommendations;
  }

  generateNextSteps() {
    const summary = this.calculateSummary();

    if (summary.readyForProduction) {
      return [
        "Deploy to production environment",
        "Test on real devices with users",
        "Monitor PWA performance metrics",
        "Set up automated PWA testing in CI/CD",
      ];
    } else {
      return [
        "Fix critical issues identified in recommendations",
        "Re-run PWA tests after fixes",
        "Test on multiple devices and browsers",
        "Optimize performance based on Lighthouse recommendations",
      ];
    }
  }

  printSummary(summary) {
    console.log("\n📊 PWA TEST SUMMARY");
    console.log("=".repeat(50));
    console.log(`Overall Score: ${summary.overallScore}/100`);
    console.log(`Status: ${summary.status}`);
    console.log(
      `Ready for Production: ${summary.readyForProduction ? "✅" : "❌"}`
    );
    console.log(`Tests Passed: ${summary.passedTests}/${summary.totalTests}`);

    if (summary.criticalIssues.length > 0) {
      console.log("\n🚨 CRITICAL ISSUES:");
      summary.criticalIssues.forEach((issue) => {
        console.log(`   ❌ ${issue}`);
      });
    }

    console.log("\n💡 Next Steps:");
    this.generateNextSteps().forEach((step, index) => {
      console.log(`   ${index + 1}. ${step}`);
    });
  }
}

// CLI execution
if (require.main === module) {
  const tester = new PWATester();

  // Check if server URL provided
  if (process.argv[2]) {
    tester.serverUrl = process.argv[2];
  }

  console.log(`🎯 Testing PWA at: ${tester.serverUrl}\n`);

  tester
    .runFullPWATest()
    .then((report) => {
      if (report) {
        console.log("\n✅ PWA testing completed successfully!");
        console.log("📄 Report saved to: pwa-test-report.json");

        // Exit with appropriate code
        process.exit(report.summary.readyForProduction ? 0 : 1);
      } else {
        console.log("\n❌ PWA testing failed!");
        process.exit(1);
      }
    })
    .catch((error) => {
      console.error("\n💥 PWA testing crashed:", error);
      process.exit(1);
    });
}

module.exports = PWATester;
