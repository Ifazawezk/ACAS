#!/usr/bin/env python3
"""
ACAS App Icons Generator
Generates placeholder icons for PWA installation on iOS (iPad/iPhone)
Run this script to create the required app icons in /frontend/icons/

Requirements: pip install pillow
"""

import os
from pathlib import Path

def generate_icons():
    """Generate placeholder app icons using PIL"""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("❌ Error: Pillow not installed")
        print("Install with: pip install pillow")
        return False
    
    # Create icons directory
    icons_dir = Path("frontend/icons")
    icons_dir.mkdir(exist_ok=True)
    
    # Brand colors
    primary_color = (31, 119, 194)  # #1F77C2
    accent_color = (220, 38, 38)    # #DC2626
    white = (255, 255, 255)
    
    print("[Icons] Generating app icons...")
    
    # Icon sizes to generate
    icon_sizes = [
        (192, '192x192'),
        (512, '512x512'),
        (1024, '1024x1024'),
    ]
    
    for size, label in icon_sizes:
        # Create base icon
        img = Image.new('RGB', (size, size), primary_color)
        draw = ImageDraw.Draw(img)
        
        # Draw a simple ACAS logo (stylized A)
        border = int(size * 0.15)
        
        # Draw circle border
        draw.ellipse(
            [border, border, size-border, size-border],
            outline=white,
            width=int(size * 0.08)
        )
        
        # Draw "A" letter in center (simplified)
        left = border + int(size * 0.1)
        right = size - border - int(size * 0.1)
        width = right - left
        
        # Triangle points for "A"
        points = [
            (left + width//2, border + int(size * 0.2)),  # top
            (left, size - border - int(size * 0.1)),       # bottom left
            (right, size - border - int(size * 0.1)),      # bottom right
        ]
        draw.polygon(points, fill=white)
        
        # Save icon
        icon_path = icons_dir / f"icon-{label}.png"
        img.save(icon_path)
        print(f"✓ Created: {icon_path}")
    
    # Generate maskable icons (for modern app displays)
    print("\n[Icons] Generating maskable icons (safe zone)...")
    for size, label in icon_sizes:
        img = Image.new('RGB', (size, size), white)
        draw = ImageDraw.Draw(img)
        
        # Maskable icon has 10% safe zone margin
        margin = int(size * 0.1)
        inner_size = size - (2 * margin)
        
        # Draw colored circle in safe zone
        draw.ellipse(
            [margin, margin, margin + inner_size, margin + inner_size],
            fill=primary_color
        )
        
        # Draw "A" on colored background
        left = margin + int(inner_size * 0.1)
        right = margin + inner_size - int(inner_size * 0.1)
        width = right - left
        
        points = [
            (left + width//2, margin + int(inner_size * 0.2)),
            (left, margin + inner_size - int(inner_size * 0.1)),
            (right, margin + inner_size - int(inner_size * 0.1)),
        ]
        draw.polygon(points, fill=white)
        
        # Save maskable icon
        icon_path = icons_dir / f"icon-maskable-{label}.png"
        img.save(icon_path)
        print(f"✓ Created: {icon_path}")
    
    # Generate splash screens for iOS
    print("\n[Icons] Generating iOS splash screens...")
    splash_sizes = [
        (1125, 2436, '1125x2436', 'iPhone 11 Pro Max'),
        (1242, 2208, '1242x2208', 'iPhone 11 Pro'),
        (2048, 2732, '2048x2732', 'iPad Pro 12.9"'),
    ]
    
    for width, height, label, device in splash_sizes:
        # Create splash with gradient
        img = Image.new('RGB', (width, height), primary_color)
        draw = ImageDraw.Draw(img)
        
        # Draw gradient-like effect (simplified)
        for y in range(height):
            ratio = y / height
            # Blend primary_color with accent_color
            r = int(primary_color[0] * (1 - ratio) + accent_color[0] * ratio)
            g = int(primary_color[1] * (1 - ratio) + accent_color[1] * ratio)
            b = int(primary_color[2] * (1 - ratio) + accent_color[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Draw app name in center
        center_y = height // 2
        text_size = int(width * 0.15)
        
        # Simple text rendering (PIL limitation)
        draw.text(
            (width // 2 - int(text_size * 1), center_y),
            "ACAS",
            fill=white,
            font=None
        )
        
        # Save splash screen
        splash_path = icons_dir / f"splash-{label}.png"
        img.save(splash_path)
        print(f"✓ Created: {splash_path} ({device})")
    
    # Generate dashboard/feature icons
    print("\n[Icons] Generating feature icons...")
    feature_icons = [
        ('dashboard', 'Dashboard', primary_color),
        ('analyze', 'Analyze', accent_color),
        ('comments', 'Comments', primary_color),
    ]
    
    for icon_name, label, color in feature_icons:
        img = Image.new('RGB', (192, 192), color)
        draw = ImageDraw.Draw(img)
        
        # Simple icon representation
        draw.rectangle([30, 30, 162, 162], outline=white, width=8)
        draw.line([(30, 60), (162, 60)], fill=white, width=4)
        draw.line([(30, 90), (162, 90)], fill=white, width=4)
        
        icon_path = icons_dir / f"{icon_name}-192x192.png"
        img.save(icon_path)
        print(f"✓ Created: {icon_path} ({label})")
    
    print("\n" + "=" * 60)
    print("✅ All icons generated successfully!")
    print("=" * 60)
    print("\nIcons created in: frontend/icons/")
    print("\nTo use custom icons:")
    print("1. Replace generated PNGs with your brand logos")
    print("2. Keep the same filenames and sizes")
    print("3. PNG format, transparent background if possible")
    print("4. Restart server and refresh app in Safari")
    print("\nIcon requirements:")
    print("- icon-192x192.png: Home screen icon")
    print("- icon-512x512.png: Splash screen icon")
    print("- icon-maskable-192x192.png: Safe zone (10% margin)")
    print("- icon-maskable-512x512.png: Safe zone version")
    print("- splash-*.png: iOS launch screens")
    print("\n✨ Your iPad app is ready to install!")
    
    return True

if __name__ == "__main__":
    generate_icons()
