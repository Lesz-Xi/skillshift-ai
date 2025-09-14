#!/usr/bin/env python3
"""
Debug script to identify hero recognition failures causing coaching feedback errors.
Based on terminal logs analysis showing hero defaulting to "unknown".
"""

import sys
import json
from pathlib import Path
import logging

# Add the skillshift-ai path
sys.path.append(str(Path(__file__).parent / "skillshift-ai"))

def analyze_screenshots_for_hero_recognition():
    """Analyze the specific screenshots causing issues"""
    print("🔍 Hero Recognition Debug Analysis")
    print("=" * 60)
    
    # Test images from the user
    test_images = [
        "Trial-Image/Kagura/DMG_Kagura.PNG",  # Damage stats view
        "Trial-Image/Kagura/KDA_Kagura.PNG"   # KDA/scoreboard view  
    ]
    
    for image_path in test_images:
        if not Path(image_path).exists():
            print(f"❌ Image not found: {image_path}")
            continue
            
        print(f"\n📸 Analyzing: {image_path}")
        
        try:
            # Test OCR text extraction
            print("🔤 Testing OCR text extraction...")
            test_ocr_extraction(image_path)
            
            # Test hero name detection
            print("🦸 Testing hero name detection...")
            test_hero_detection(image_path)
            
            # Test IGN matching
            print("👤 Testing IGN matching...")
            test_ign_matching(image_path)
            
        except Exception as e:
            print(f"❌ Error analyzing {image_path}: {e}")
            import traceback
            traceback.print_exc()

def test_ocr_extraction(image_path):
    """Test basic OCR text extraction"""
    try:
        from core.enhanced_data_collector import EnhancedDataCollector
        
        collector = EnhancedDataCollector()
        result = collector.analyze_screenshot_with_session(
            image_path=image_path,
            ign="Lesz XVII",
            session_id="debug_session"
        )
        
        print(f"   ✅ OCR Success: {result.get('success', False)}")
        print(f"   📊 Confidence: {result.get('overall_confidence', 0)}")
        
        # Check if hero was detected
        hero = result.get('data', {}).get('hero', 'NOT_FOUND')
        print(f"   🦸 Hero detected: {hero}")
        
        if hero == 'unknown' or hero == 'NOT_FOUND':
            print("   ⚠️  ISSUE: Hero recognition failed!")
            
            # Check raw OCR text for manual inspection
            debug_info = result.get('debug_info', {})
            if 'ocr_text_preview' in debug_info:
                preview = debug_info['ocr_text_preview'][:200]
                print(f"   📝 OCR Text Preview: {preview}...")
        
        return result
        
    except Exception as e:
        print(f"   ❌ OCR Test Failed: {e}")
        return None

def test_hero_detection(image_path):
    """Test specific hero detection methods"""
    try:
        from core.hero_identifier import HeroIdentifier
        
        identifier = HeroIdentifier()
        
        # Test with expected hero name
        expected_heroes = ["kagura", "Kagura", "KAGURA"]
        
        for test_hero in expected_heroes:
            hero, confidence = identifier.identify_hero(test_hero)
            print(f"   🎯 Test '{test_hero}' → '{hero}' (confidence: {confidence:.3f})")
            
            if confidence >= 0.7:
                print(f"   ✅ Hero identification would succeed")
                return True
        
        print("   ❌ All hero identification tests failed")
        return False
        
    except Exception as e:
        print(f"   ❌ Hero Detection Test Failed: {e}")
        return False

def test_ign_matching(image_path):
    """Test IGN matching logic"""
    try:
        from core.enhanced_data_collector import RobustIGNMatcher
        
        # Test IGN variations that might be causing issues
        test_igns = ["Lesz XVII", "Lesz 17", "17", "XVII", "lesz xvii"]
        
        matcher = RobustIGNMatcher()
        
        # Simulate OCR results that might be found
        mock_ocr_results = [
            {"text": "Lesz XVII", "confidence": 0.9},
            {"text": "17", "confidence": 0.8},
            {"text": "XVII", "confidence": 0.7},
            {"text": "Lesz", "confidence": 0.85}
        ]
        
        for test_ign in test_igns:
            result = matcher._partial_match(test_ign, mock_ocr_results)
            print(f"   🔍 IGN '{test_ign}' → {result}")
            
            if result.get('found', False):
                print(f"   ✅ IGN matching would succeed")
                return True
        
        print("   ⚠️  IGN matching may be problematic")
        return False
        
    except Exception as e:
        print(f"   ❌ IGN Matching Test Failed: {e}")
        return False

def diagnose_coaching_system():
    """Test coaching system with known good data"""
    print("\n🧠 Testing Coaching System")
    print("=" * 40)
    
    # Test data that mimics what should be extracted from the screenshots
    test_match_data = {
        "hero": "kagura",  # Test with known hero
        "kills": 9,
        "deaths": 2, 
        "assists": 12,
        "gold": 12374,
        "hero_damage": 107100,
        "turret_damage": 2854,
        "damage_taken": 54444,
        "teamfight_participation": 70,
        "match_duration": 21.12,
        "rank": "epic"
    }
    
    try:
        from core.enhanced_coach_bridge import EnhancedCoachBridge
        
        coach_bridge = EnhancedCoachBridge()
        
        print(f"📊 Test Data: {json.dumps(test_match_data, indent=2)}")
        
        # Test coaching generation
        coaching_result = coach_bridge.generate_enhanced_feedback(
            match_data=test_match_data,
            include_severity=True
        )
        
        print(f"✅ Coaching Generation: {len(coaching_result) > 0}")
        
        if len(coaching_result) > 0:
            feedback_count = len(coaching_result)
            print(f"📝 Generated {feedback_count} feedback items")
            for i, feedback in enumerate(coaching_result[:3]):  # Show first 3
                if isinstance(feedback, tuple):
                    severity, message = feedback
                    print(f"   {i+1}. [{severity}] {message}")
                else:
                    print(f"   {i+1}. {feedback}")
        else:
            print(f"❌ Coaching Error: No feedback generated")
        
        return coaching_result
        
    except Exception as e:
        print(f"❌ Coaching System Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_unknown_hero():
    """Test what happens with unknown hero (current failing scenario)"""
    print("\n🚨 Testing Unknown Hero Scenario")
    print("=" * 40)
    
    test_match_data = {
        "hero": "unknown",  # This is what's currently happening
        "kills": 9,
        "deaths": 2,
        "assists": 12,
        "gold": 12374,
        "hero_damage": 107100,
        "turret_damage": 2854,
        "damage_taken": 54444,
        "teamfight_participation": 70,
        "match_duration": 21.12,
        "rank": "epic"
    }
    
    try:
        from core.enhanced_coach_bridge import EnhancedCoachBridge
        
        coach_bridge = EnhancedCoachBridge()
        
        print(f"📊 Testing with hero='unknown'")
        
        coaching_result = coach_bridge.generate_enhanced_feedback(
            match_data=test_match_data,
            include_severity=True
        )
        
        print(f"Result: {len(coaching_result) > 0}")
        
        if len(coaching_result) == 0:
            print(f"🎯 ROOT CAUSE IDENTIFIED: No feedback generated for unknown hero")
            print("This is likely the exact error you're seeing!")
        else:
            print(f"✅ SUCCESS: Generated {len(coaching_result)} feedback items for unknown hero")
            for i, feedback in enumerate(coaching_result[:2]):  # Show first 2
                if isinstance(feedback, tuple):
                    severity, message = feedback
                    print(f"   {i+1}. [{severity}] {message}")
                else:
                    print(f"   {i+1}. {feedback}")
        
        return coaching_result
        
    except Exception as e:
        error_msg = str(e)
        print(f"🎯 ROOT CAUSE IDENTIFIED: {error_msg}")
        print("This exception is likely the coaching feedback error!")
        import traceback
        traceback.print_exc()
        return None

def provide_solutions():
    """Provide specific solutions based on findings"""
    print("\n🔧 RECOMMENDED SOLUTIONS")
    print("=" * 40)
    
    print("1. 🦸 IMMEDIATE FIX - Hero Override:")
    print("   - Use the 'Optional Hero Override' field in the UI")
    print("   - Enter 'Kagura' manually when uploading screenshots")
    print("   - This bypasses hero recognition entirely")
    
    print("\n2. 📝 HERO RECOGNITION IMPROVEMENT:")
    print("   - The OCR is likely having trouble reading 'Kagura' from your screenshots")
    print("   - Try uploading clearer screenshots if possible")
    print("   - Ensure hero names are clearly visible")
    
    print("\n3. 🛡️  COACHING SYSTEM ROBUSTNESS:")
    print("   - Add fallback coaching for 'unknown' heroes")
    print("   - Improve error handling in coaching generation")
    print("   - Create generic coaching templates")
    
    print("\n4. 🔍 DEBUG LOGGING:")
    print("   - Enable detailed logging to see exact OCR text")
    print("   - Check what hero names are being extracted")
    print("   - Monitor IGN matching success rates")

if __name__ == "__main__":
    print("🚨 COACHING FEEDBACK ERROR DIAGNOSTIC")
    print("Analyzing hero recognition failures causing coaching errors")
    print("=" * 70)
    
    # Run comprehensive diagnosis
    analyze_screenshots_for_hero_recognition()
    diagnose_coaching_system()
    test_with_unknown_hero()
    provide_solutions()
    
    print("\n" + "=" * 70)
    print("✅ DIAGNOSIS COMPLETE")
    print("Check the output above for specific error causes and solutions")
    print("The most likely fix is to use the Hero Override feature!")
