#!/usr/bin/env python3
"""
Test different parameter combinations for subtle fish-eye effect
"""
import requests
import json

API_BASE = "http://localhost:8080"

def test_subtle_fisheye_parameters():
    """Test parameter combinations for subtle non-circular fish-eye effect"""
    print("=== Testing Subtle Fish-Eye Parameter Combinations ===")
    print()
    
    # Test different parameter combinations
    test_configs = [
        {
            "name": "Very Subtle Fish-Eye (Recommended)",
            "description": "Minimal distortion, no vignette, no circular crop",
            "params": {
                "distortion_strength": 0.2,
                "zoom_factor": 1.0,
                "circular_crop": False,
                "vignette_intensity": 0.0,
                "center_x": 0.5,
                "center_y": 0.5
            }
        },
        {
            "name": "Light Fish-Eye Distortion",
            "description": "Light distortion with minimal zoom",
            "params": {
                "distortion_strength": 0.3,
                "zoom_factor": 1.05,
                "circular_crop": False,
                "vignette_intensity": 0.0,
                "center_x": 0.5,
                "center_y": 0.5
            }
        },
        {
            "name": "Moderate Wide-Angle Effect",
            "description": "More noticeable but still subtle distortion",
            "params": {
                "distortion_strength": 0.4,
                "zoom_factor": 1.1,
                "circular_crop": False,
                "vignette_intensity": 0.1,
                "center_x": 0.5,
                "center_y": 0.5
            }
        },
        {
            "name": "Off-Center Subtle Effect",
            "description": "Subtle distortion with off-center focus",
            "params": {
                "distortion_strength": 0.25,
                "zoom_factor": 1.0,
                "circular_crop": False,
                "vignette_intensity": 0.0,
                "center_x": 0.6,
                "center_y": 0.4
            }
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"{i}. {config['name']}")
        print(f"   Description: {config['description']}")
        print(f"   Parameters:")
        for param, value in config['params'].items():
            print(f"     - {param}: {value}")
        print()
    
    print("🎯 Key Parameter Guidelines for Subtle Fish-Eye:")
    print("   • distortion_strength: 0.1-0.4 (lower = more subtle)")
    print("   • zoom_factor: 1.0-1.1 (1.0 = no zoom, reduces circular effect)")
    print("   • circular_crop: false (prevents circular masking)")
    print("   • vignette_intensity: 0.0-0.1 (0.0 = no darkening at edges)")
    print("   • center_x/y: 0.5 (centered) or adjust for creative effects")
    print()
    
    print("🔧 Recommended Starting Point:")
    print("   For the most subtle, non-circular fish-eye effect, use:")
    recommended = test_configs[0]['params']
    print("   {")
    for param, value in recommended.items():
        if isinstance(value, bool):
            print(f'     "{param}": {str(value).lower()},')
        else:
            print(f'     "{param}": {value},')
    print("   }")

if __name__ == "__main__":
    test_subtle_fisheye_parameters()