#!/usr/bin/env python3
"""
Comprehensive build script for Salford theme assets.
Supports different modes: copy, watch, and full build.
"""
import os
import sys
import time
import shutil
from pathlib import Path

# Try to import optional dependencies
try:
    import sass
    SASS_AVAILABLE = True
except ImportError:
    SASS_AVAILABLE = False

try:
    from jsmin import jsmin
    JSMIN_AVAILABLE = True
except ImportError:
    JSMIN_AVAILABLE = False

# Try to import Django settings, but don't fail if not available
try:
    from django.conf import settings
    from django.core.management import call_command
    from journal import models as journal_models
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Mock settings for standalone mode
    class MockSettings:
        BASE_DIR = Path(__file__).parent.parent.parent
    settings = MockSettings()

# Get the base directory (src folder)
BASE_DIR = Path(__file__).parent.parent.parent


def copy_css_assets():
    """Copy CSS files from theme assets to static directory"""
    source_css = BASE_DIR / "themes" / "salford" / "assets" / "css" / "salford.css"
    dest_dir = BASE_DIR / "static" / "salford" / "css"
    dest_css = dest_dir / "salford.css"
    
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy the CSS file
    if source_css.exists():
        shutil.copy2(source_css, dest_css)
        print(f"✅ Copied {source_css} to {dest_css}")
        return True
    else:
        print(f"❌ Source CSS file not found: {source_css}")
        return False


def copy_all_assets():
    """Copy all theme assets to static directory"""
    source_dir = BASE_DIR / "themes" / "salford" / "assets"
    dest_dir = BASE_DIR / "static" / "salford"
    
    if source_dir.exists():
        # Copy the entire assets directory
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(source_dir, dest_dir)
        print(f"✅ Copied all assets from {source_dir} to {dest_dir}")
        return True
    else:
        print(f"❌ Source assets directory not found: {source_dir}")
        return False


def watch_and_copy():
    """Watch for changes in the CSS file and copy automatically"""
    source_css = BASE_DIR / "themes" / "salford" / "assets" / "css" / "salford.css"
    
    if not source_css.exists():
        print(f"❌ Source CSS file not found: {source_css}")
        return
    
    print(f"👀 Watching for changes in: {source_css}")
    print("Press Ctrl+C to stop watching")
    
    last_modified = source_css.stat().st_mtime
    
    try:
        while True:
            current_modified = source_css.stat().st_mtime
            
            if current_modified > last_modified:
                print(f"\n🔄 File changed at {time.strftime('%H:%M:%S')}")
                if copy_css_assets():
                    print("✅ CSS updated successfully!")
                last_modified = current_modified
            
            time.sleep(1)  # Check every second
            
    except KeyboardInterrupt:
        print("\n👋 Stopped watching for changes")


def process_scss():
    """Compiles SCSS into CSS in the Static Assets folder"""
    if not DJANGO_AVAILABLE:
        print("⚠️  Django not available, skipping SCSS processing")
        return
    
    if not SASS_AVAILABLE:
        print("⚠️  Sass not available, skipping SCSS processing")
        return
    
    paths = [
        BASE_DIR / "themes/salford/assets/foundation-sites/scss/",
        BASE_DIR / "themes/salford/assets/motion-ui/src/",
    ]

    # File dirs
    app_scss_file = BASE_DIR / "themes/salford/assets/scss/app.scss"
    app_css_file = BASE_DIR / "static/salford/css/app.css"

    if app_scss_file.exists():
        compiled_css_from_file = sass.compile(filename=str(app_scss_file), include_paths=[str(p) for p in paths])
        
        # Open the CSS file and write into it
        with open(app_css_file, "w", encoding="utf-8") as write_file:
            write_file.write(compiled_css_from_file)
        print(f"✅ Compiled SCSS: {app_scss_file} -> {app_css_file}")
    else:
        print(f"⚠️  SCSS file not found: {app_scss_file}")


def process_js():
    """Copies JS from compile into static assets"""
    if not DJANGO_AVAILABLE:
        print("⚠️  Django not available, skipping JS processing")
        return
    
    source_paths = [
        BASE_DIR / "themes/salford/assets/js/admin.js",
        BASE_DIR / "themes/salford/assets/js/app.js",
        BASE_DIR / "themes/salford/assets/js/footnotes.js",
        BASE_DIR / "themes/salford/assets/js/table_of_contents.js",
        BASE_DIR / "themes/salford/assets/js/text_resize.js",
        BASE_DIR / "themes/salford/assets/js/toastr.js",
    ]
    dest_path = BASE_DIR / "static/salford/js/app.js"
    min_path = BASE_DIR / "static/salford/js/app.min.js"

    # Create destination directory
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy existing JS files
    existing_files = [p for p in source_paths if p.exists()]
    if existing_files:
        with open(dest_path, "w", encoding="utf-8") as f:
            for src_file in existing_files:
                with open(src_file, "r", encoding="utf-8") as input_file:
                    f.write(input_file.read())
        print(f"✅ Processed JS files -> {dest_path}")
    else:
        print("⚠️  No JS files found to process")


def process_journals(override_css_dir, paths):
    """Processes journal-specific CSS overrides"""
    if not DJANGO_AVAILABLE:
        print("⚠️  Django not available, skipping journal overrides")
        return
    
    if not SASS_AVAILABLE:
        print("⚠️  Sass not available, skipping journal overrides")
        return
    
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        journal_dir = BASE_DIR / "files" / "styling" / "journals" / str(journal.id)
        scss_files = []

        if journal_dir.exists():
            for file in journal_dir.iterdir():
                if file.suffix == ".scss":
                    scss_files.append(file)

        if scss_files:
            print(f"📝 Journal {journal.id} [{journal.name}]: processing overrides")
            override_css_file = override_css_dir / f"journal{journal.id}_override.css"
            
            # Process the first SCSS file
            compiled_css_from_file = sass.compile(
                filename=str(scss_files[0]), 
                include_paths=[str(p) for p in paths]
            )
            
            with open(override_css_file, "w", encoding="utf-8") as write_file:
                write_file.write(compiled_css_from_file)


def create_paths():
    """Create necessary directories"""
    base_path = BASE_DIR / "static" / "salford"
    folders = ["css", "js", "fonts", "img"]

    for folder in folders:
        (base_path / folder).mkdir(parents=True, exist_ok=True)

    # Create journal CSS directory
    override_css_dir = base_path / "css"
    override_css_dir.mkdir(parents=True, exist_ok=True)

    return override_css_dir


def build_full():
    """Full build process with all features"""
    print("🏗️  Starting full build process...")
    
    override_css_dir = create_paths()
    
    print("📋 Copying CSS assets...")
    copy_css_assets()
    
    print("📋 Copying all assets...")
    copy_all_assets()
    
    print("🎨 Processing SCSS...")
    process_scss()
    
    print("⚡ Processing JS...")
    process_js()
    
    if DJANGO_AVAILABLE:
        print("📝 Processing journal overrides...")
        include_paths = [
            BASE_DIR / "themes/salford/assets/foundation-sites/scss/",
            BASE_DIR / "themes/salford/assets/motion-ui/src/",
        ]
        process_journals(override_css_dir, include_paths)
        
        print("📦 Running collectstatic...")
        call_command("collectstatic", "--noinput")
    
    print("✅ Full build completed!")


def build_simple():
    """Simple build - just copy assets"""
    print("📋 Starting simple build (copy assets only)...")
    
    copy_css_assets()
    copy_all_assets()
    
    print("✅ Simple build completed!")


def show_help():
    """Show usage information"""
    print("🎨 Salford Theme Build Script")
    print("=" * 40)
    print("Usage: python build_assets.py [mode]")
    print()
    print("Modes:")
    print("  copy     - Copy CSS and all assets (default)")
    print("  watch    - Watch for CSS changes and auto-copy")
    print("  build    - Full build with SCSS, JS, and Django features")
    print("  help     - Show this help message")
    print()
    print("Examples:")
    print("  python build_assets.py copy    # Copy assets once")
    print("  python build_assets.py watch   # Watch for changes")
    print("  python build_assets.py build   # Full build process")


def main():
    """Main entry point"""
    mode = sys.argv[1] if len(sys.argv) > 1 else "copy"
    
    if mode == "help" or mode == "--help" or mode == "-h":
        show_help()
        return
    
    elif mode == "copy":
        build_simple()
    
    elif mode == "watch":
        print("🎨 Salford Theme CSS Watcher")
        print("=" * 40)
        print("📋 Performing initial copy...")
        copy_css_assets()
        watch_and_copy()
    
    elif mode == "build":
        build_full()
    
    else:
        print(f"❌ Unknown mode: {mode}")
        show_help()


if __name__ == "__main__":
    main()
