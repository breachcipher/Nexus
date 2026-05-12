#!/bin/bash
set -e

# Configuration
PACKAGE_NAME="lazyframework"
VERSION="2.6.0"
SOURCE_DIR="/usr/share/lazyframework"
BUILD_DIR="$HOME/lazyframework-deb-temp"
DEB_FILE="$HOME/lazyframework_${VERSION}_all.deb"

# Colors for output
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
MAGENTA='\033[1;35m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║             LazyFramework .deb Builder v2.6.0            ║"
echo "║               (PyQt6 Dependency Fix)                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}[!] ERROR: Source directory not found: $SOURCE_DIR${NC}"
    echo -e "${YELLOW}[*] Please install LazyFramework first:${NC}"
    echo -e "    ${GREEN}sudo make install${NC}"
    echo -e "    or run from the source directory"
    exit 1
fi

# Check system distribution
echo -e "${BLUE}[+] Detecting system distribution...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION_ID=$VERSION_ID
    echo -e "    ${GREEN}Distribution: ${CYAN}$PRETTY_NAME${NC}"
else
    OS=$(uname -s)
    echo -e "    ${YELLOW}Distribution: ${CYAN}$OS${NC}"
fi

# Clean previous builds
echo -e "${BLUE}[+] Cleaning previous build...${NC}"
rm -rf "$BUILD_DIR" "$DEB_FILE" 2>/dev/null || true

# Create directory structure
echo -e "${BLUE}[+] Creating directory structure...${NC}"
mkdir -p "$BUILD_DIR/DEBIAN" \
         "$BUILD_DIR/usr/bin" \
         "$BUILD_DIR/usr/share/$PACKAGE_NAME" \
         "$BUILD_DIR/usr/share/applications" \
         "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps" \
         "$BUILD_DIR/usr/share/doc/$PACKAGE_NAME"

# Copy source files (EXCLUDE __pycache__ and .pyc files)
echo -e "${BLUE}[+] Copying framework files...${NC}"
# First, clean the source directory from cache files
find "$SOURCE_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$SOURCE_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Copy files using tar to preserve structure and exclude patterns
cd "$SOURCE_DIR" && tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' -cf - . | \
    (cd "$BUILD_DIR/usr/share/$PACKAGE_NAME" && tar xf -) 2>/dev/null || \
    cp -r "$SOURCE_DIR"/* "$BUILD_DIR/usr/share/$PACKAGE_NAME/" 2>/dev/null || true

# Double check for cache files
find "$BUILD_DIR/usr/share/$PACKAGE_NAME" -name "*.pyc" -delete 2>/dev/null || true
find "$BUILD_DIR/usr/share/$PACKAGE_NAME" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Create launcher scripts
echo -e "${BLUE}[+] Creating launchers...${NC}"

# GUI Launcher
cat > "$BUILD_DIR/usr/bin/lazyframework" << 'EOF'
#!/bin/bash
# LazyFramework GUI Launcher

# Check if running in Termux
if [ -d "/data/data/com.termux" ]; then
    echo "Running in Termux environment"
    cd /data/data/com.termux/files/home/lazyframework 2>/dev/null || cd /usr/share/lazyframework
else
    cd /usr/share/lazyframework 2>/dev/null || {
        echo "Error: LazyFramework not found in /usr/share/lazyframework"
        exit 1
    }
fi

# Check Python dependencies
echo "Checking dependencies..."
python3 -c "import PyQt6, sys; print('PyQt6:', PyQt6.__version__)" 2>/dev/null || {
    echo "Installing PyQt6 dependencies..."
    pip3 install --quiet PyQt6 PyQt6-WebEngine 2>/dev/null || {
        echo "Failed to install PyQt6. Please install manually:"
        echo "  pip3 install PyQt6 PyQt6-WebEngine"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]] || exit 1
    }
}

# Launch the framework
exec python3 lzfconsole --gui "$@"
EOF

# Console Launcher
cat > "$BUILD_DIR/usr/bin/lzfconsole" << 'EOF'
#!/bin/bash
# LazyFramework Console Launcher

# Check if running in Termux
if [ -d "/data/data/com.termux" ]; then
    echo "Running in Termux environment"
    cd /data/data/com.termux/files/home/lazyframework 2>/dev/null || cd /usr/share/lazyframework
else
    cd /usr/share/lazyframework 2>/dev/null || {
        echo "Error: LazyFramework not found in /usr/share/lazyframework"
        exit 1
    }
fi

# Check Python dependencies
echo "Checking dependencies..."
python3 -c "import rich, stem, requests; print('Dependencies OK')" 2>/dev/null || {
    echo "Installing dependencies..."
    pip3 install --quiet rich stem requests 2>/dev/null || {
        echo "Some dependencies missing. Trying to continue..."
    }
}

# Launch the framework
exec python3 lzfconsole "$@"
EOF

chmod 0755 "$BUILD_DIR/usr/bin/lazyframework"
chmod 0755 "$BUILD_DIR/usr/bin/lzfconsole"

# Create SVG icon
echo -e "${BLUE}[+] Creating SVG icon...${NC}"
cat > "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/lazyframework.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#0d1117" rx="30"/>
  <rect x="28" y="28" width="200" height="200" fill="#161b22" rx="15"/>
  <text x="128" y="105" text-anchor="middle" font-family="Arial, sans-serif" font-size="36" font-weight="bold" fill="#50fa7b">LF</text>
  <text x="128" y="145" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#8be9fd">Framework</text>
  <path d="M60 170 H196 M60 185 H180 M60 200 H160" stroke="#6272a4" stroke-width="4" stroke-linecap="round"/>
</svg>
EOF

# Create changelog
echo -e "${BLUE}[+] Creating documentation...${NC}"
cat > "$BUILD_DIR/usr/share/doc/$PACKAGE_NAME/changelog.Debian" << EOF
lazyframework (${VERSION}) stable; urgency=medium

  * Version ${VERSION} release
  * Fixed PyQt6 dependency handling
  * Improved launcher scripts
  * Better cross-platform support
  * Enhanced error handling

 -- LazyFramework Team <contact@lazyframework.io>  $(date -R)
EOF
gzip -9 "$BUILD_DIR/usr/share/doc/$PACKAGE_NAME/changelog.Debian"

# Create copyright file
cat > "$BUILD_DIR/usr/share/doc/$PACKAGE_NAME/copyright" << 'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: lazyframework
Source: https://github.com/lazyhackers/lazyframework

Files: *
Copyright: 2023-2024 LazyFramework Team
License: GPL-3.0+

License: GPL-3.0+
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 .
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 .
 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
EOF

# Calculate installed size
echo -e "${BLUE}[+] Calculating package size...${NC}"
INSTALLED_SIZE=$(du -sk "$BUILD_DIR/usr" 2>/dev/null | cut -f1 || echo "1024")

# Create control file with appropriate dependencies based on OS
echo -e "${BLUE}[+] Creating control file...${NC}"

# Different dependency handling for different distros
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    # Ubuntu/Debian - PyQt6 may not be in main repos, so we make it optional
    DEPENDS="python3 (>= 3.8), python3-pip, python3-rich"
    RECOMMENDS="python3-pyqt6, python3-pyqt6.qtwebengine, tor, python3-stem, python3-requests"
elif [ "$OS" = "kali" ]; then
    # Kali Linux
    DEPENDS="python3 (>= 3.8), python3-pip"
    RECOMMENDS="python3-pyqt6, python3-pyqt6-webengine, tor, python3-rich, python3-stem, python3-requests"
else
    # Generic - minimal dependencies
    DEPENDS="python3 (>= 3.8), python3-pip"
    RECOMMENDS="tor, python3-rich, python3-stem, python3-requests"
fi

cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: net
Priority: optional
Architecture: all
Depends: $DEPENDS
Recommends: $RECOMMENDS
Suggests: nmap, sqlmap, hydra, metasploit-framework, wireshark, john, hashcat
Installed-Size: $INSTALLED_SIZE
Maintainer: LazyFramework Team <contact@lazyframework.io>
Homepage: https://github.com/lazyhackers/lazyframework
Description: Professional penetration testing framework
 LazyFramework is an advanced, open-source penetration testing
 and red team operations framework featuring both console and
 GUI interfaces.
 .
 Features:
  • Rich-based console interface
  • PyQt6 GUI with theme support (optional)
  • Modular architecture
  • Built-in proxy support
  • Cross-platform compatibility
  • Easy module development
 .
 Note: PyQt6 for GUI is optional. Framework works in console mode
 without PyQt6.
EOF

# Create desktop entry
echo -e "${BLUE}[+] Creating desktop entry...${NC}"
cat > "$BUILD_DIR/usr/share/applications/lazyframework.desktop" << 'EOF'
[Desktop Entry]
Name=LazyFramework
GenericName=Penetration Testing Framework
Comment=Professional Security Testing Framework
Exec=lazyframework
Icon=lazyframework
Terminal=false
Type=Application
Categories=Security;Utility;Development;
Keywords=security;pentest;hacking;framework;
StartupNotify=true
StartupWMClass=LazyFrameworkGUI
EOF

# Create postinst script with dependency installation
echo -e "${BLUE}[+] Creating post-installation script...${NC}"
cat > "$BUILD_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Colors for output
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
MAGENTA='\033[1;35m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                LazyFramework Post-Install                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION_CODENAME=$VERSION_CODENAME
else
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
fi

echo -e "${BLUE}[*] Detected OS: ${CYAN}$OS${NC}"

# Function to install PyQt6 based on OS
install_pyqt6() {
    echo -e "${BLUE}[*] Attempting to install PyQt6 for GUI support...${NC}"
    
    case "$OS" in
        ubuntu|debian|kali|linuxmint)
            # Try to install from apt first
            if command -v apt-get >/dev/null 2>&1; then
                echo -e "${YELLOW}[*] Checking for PyQt6 in repositories...${NC}"
                apt-get update >/dev/null 2>&1
                
                # Try different package names
                for pkg in python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6-webengine; do
                    if apt-cache show "$pkg" >/dev/null 2>&1; then
                        echo -e "${GREEN}[+] Found $pkg, installing...${NC}"
                        apt-get install -y "$pkg" 2>/dev/null || true
                    fi
                done
            fi
            ;;
        fedora|centos|rhel)
            if command -v dnf >/dev/null 2>&1; then
                dnf install -y python3-qt6 2>/dev/null || true
            elif command -v yum >/dev/null 2>&1; then
                yum install -y python3-qt6 2>/dev/null || true
            fi
            ;;
        arch|manjaro)
            if command -v pacman >/dev/null 2>&1; then
                pacman -Sy --noconfirm python-pyqt6 python-pyqt6-webengine 2>/dev/null || true
            fi
            ;;
    esac
    
    # Fallback to pip if system packages not available
    if ! python3 -c "import PyQt6" 2>/dev/null; then
        echo -e "${YELLOW}[*] PyQt6 not in repositories, trying pip...${NC}"
        if command -v pip3 >/dev/null 2>&1; then
            pip3 install --quiet PyQt6 PyQt6-WebEngine 2>/dev/null || {
                echo -e "${YELLOW}[!] Could not install PyQt6 via pip${NC}"
                echo -e "${YELLOW}[!] GUI mode will not be available${NC}"
                echo -e "${YELLOW}[!] You can install it manually later:${NC}"
                echo -e "    ${CYAN}pip3 install PyQt6 PyQt6-WebEngine${NC}"
            }
        fi
    fi
}

# Install Python dependencies
echo -e "${BLUE}[*] Installing Python dependencies...${NC}"

# Install pip dependencies
if command -v pip3 >/dev/null 2>&1; then
    echo -e "${YELLOW}[*] Installing required Python packages...${NC}"
    
    # Install basic dependencies
    for pkg in rich stem requests; do
        python3 -c "import $pkg" 2>/dev/null || {
            echo -e "${BLUE}[*] Installing $pkg...${NC}"
            pip3 install --quiet "$pkg" 2>/dev/null || true
        }
    done
    
    # Try to install PyQt6 (optional)
    read -p "Do you want to install PyQt6 for GUI support? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_pyqt6
    else
        echo -e "${YELLOW}[*] Skipping PyQt6 installation${NC}"
        echo -e "${YELLOW}[*] Console mode will still work${NC}"
    fi
else
    echo -e "${RED}[!] pip3 not found${NC}"
    echo -e "${YELLOW}[*] Installing python3-pip...${NC}"
    if command -v apt-get >/dev/null 2>&1; then
        apt-get install -y python3-pip 2>/dev/null || true
    elif command -v yum >/dev/null 2>&1; then
        yum install -y python3-pip 2>/dev/null || true
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y python3-pip 2>/dev/null || true
    elif command -v pacman >/dev/null 2>&1; then
        pacman -Sy --noconfirm python-pip 2>/dev/null || true
    fi
    
    # Try pip3 again
    if command -v pip3 >/dev/null 2>&1; then
        pip3 install --quiet rich stem requests 2>/dev/null || true
    fi
fi

# Update icon cache
echo -e "${BLUE}[*] Updating icon cache...${NC}"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
    echo -e "${GREEN}[+] Icon cache updated${NC}"
fi

# Update desktop database
echo -e "${BLUE}[*] Updating desktop database...${NC}"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications 2>/dev/null || true
    echo -e "${GREEN}[+] Desktop database updated${NC}"
fi

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                INSTALLATION COMPLETE!                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}✅ LazyFramework ${VERSION} has been successfully installed!${NC}"
echo ""
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Usage Instructions:${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}🎯 Console Mode (always available):${NC}"
echo -e "   ${GREEN}lzfconsole${NC}           # Start framework in terminal"
echo -e "   ${GREEN}lzfconsole --help${NC}    # Show help"
echo ""
echo -e "${CYAN}🖥️  GUI Mode (requires PyQt6):${NC}"
echo -e "   ${GREEN}lazyframework${NC}        # Start with GUI"
echo ""
echo -e "${CYAN}🔧 Check Installation:${NC}"
echo -e "   ${GREEN}python3 -c \"import rich; print('Rich:', rich.__version__)\"${NC}"
echo -e "   ${GREEN}python3 -c \"import PyQt6; print('PyQt6:', PyQt6.__version__)\"${NC}"
echo ""
echo -e "${CYAN}📦 Install Missing Dependencies:${NC}"
echo -e "   ${GREEN}pip3 install PyQt6 PyQt6-WebEngine${NC}  # For GUI"
echo -e "   ${GREEN}sudo apt install python3-pyqt6${NC}      # On Debian/Ubuntu"
echo ""
echo -e "${YELLOW}Note:${NC} If GUI doesn't work, use ${CYAN}lzfconsole${NC} for terminal mode."
echo -e "All core features are available in console mode."
echo ""

exit 0
EOF

# Create prerm script
cat > "$BUILD_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

echo "[*] Preparing to remove LazyFramework..."
exit 0
EOF

# Create postrm script
cat > "$BUILD_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    purge|remove|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)
        # Update icon cache
        if command -v gtk-update-icon-cache >/dev/null 2>&1; then
            gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
        fi
        
        # Update desktop database
        if command -v update-desktop-database >/dev/null 2>&1; then
            update-desktop-database -q /usr/share/applications 2>/dev/null || true
        fi
        ;;
esac

exit 0
EOF

# Set executable permissions for maintainer scripts
echo -e "${BLUE}[+] Setting permissions...${NC}"
chmod 0755 "$BUILD_DIR/DEBIAN/postinst"
chmod 0755 "$BUILD_DIR/DEBIAN/prerm"
chmod 0755 "$BUILD_DIR/DEBIAN/postrm"
chmod 0644 "$BUILD_DIR/DEBIAN/control"

# Fix all permissions
echo -e "${BLUE}[+] Fixing file permissions...${NC}"
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
find "$BUILD_DIR/usr" -type f -exec chmod 644 {} \;
chmod 755 "$BUILD_DIR/usr/bin"/* 2>/dev/null || true

# Make sure main Python script is executable if it exists
if [ -f "$BUILD_DIR/usr/share/$PACKAGE_NAME/lzfconsole" ]; then
    chmod 755 "$BUILD_DIR/usr/share/$PACKAGE_NAME/lzfconsole"
fi

# Build the package
echo -e "${BLUE}[+] Building .deb package...${NC}"
echo -e "${YELLOW}This may take a moment...${NC}"

# Build package
if dpkg-deb --build --root-owner-group -Zgzip "$BUILD_DIR" "$DEB_FILE" 2>/dev/null; then
    echo -e "${GREEN}[+] Package built successfully${NC}"
else
    # Try with fakeroot if available
    if command -v fakeroot >/dev/null 2>&1; then
        echo -e "${YELLOW}[*] Trying with fakeroot...${NC}"
        fakeroot dpkg-deb --build -Zgzip "$BUILD_DIR" "$DEB_FILE" 2>/dev/null || {
            echo -e "${RED}[!] Package build failed${NC}"
            exit 1
        }
    else
        echo -e "${RED}[!] Package build failed${NC}"
        exit 1
    fi
fi

# Verify the package
echo -e "${BLUE}[+] Verifying package...${NC}"
if command -v dpkg-deb >/dev/null 2>&1 && [ -f "$DEB_FILE" ]; then
    PACKAGE_SIZE=$(du -h "$DEB_FILE" | cut -f1)
    FILE_COUNT=$(dpkg-deb -c "$DEB_FILE" | wc -l)
    
    echo -e "${GREEN}[+] Package created successfully!${NC}"
    echo -e "    📦 Size: $PACKAGE_SIZE"
    echo -e "    📄 Files: $FILE_COUNT"
    
    # Show control information
    echo -e "\n${YELLOW}Package Information:${NC}"
    dpkg-deb -I "$DEB_FILE" | grep -E "(Package|Version|Depends|Recommends|Description)"
else
    echo -e "${YELLOW}[*] Could not verify package, but file was created${NC}"
fi

# Clean up
echo -e "${BLUE}[+] Cleaning up temporary files...${NC}"
rm -rf "$BUILD_DIR"

# Display success message
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    PACKAGE BUILD SUCCESSFUL!                 ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  📦 Package: $DEB_FILE"
echo "║  📊 Size:    $(du -h "$DEB_FILE" 2>/dev/null | cut -f1 || echo "Unknown")"
echo "║  🏷️  Version: $VERSION"
echo "║  🐧 Distro:   $(lsb_release -ds 2>/dev/null || echo "Generic Linux")"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}Installation Instructions:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}1. Install the package:${NC}"
echo -e "   ${GREEN}sudo dpkg -i \"$DEB_FILE\"${NC}"
echo ""
echo -e "${YELLOW}2. If PyQt6 is not available (common on Debian/Ubuntu):${NC}"
echo -e "   ${GREEN}sudo apt install -f${NC}"
echo -e "   ${GREEN}pip3 install PyQt6 PyQt6-WebEngine${NC}"
echo ""
echo -e "${YELLOW}3. Alternative installation method:${NC}"
echo -e "   ${GREEN}sudo dpkg -i --force-depends \"$DEB_FILE\"${NC}"
echo -e "   ${GREEN}sudo apt install -f${NC}"
echo ""
echo -e "${YELLOW}4. Test installation:${NC}"
echo -e "   ${GREEN}lzfconsole --help${NC}        # Test console mode"
echo -e "   ${GREEN}python3 -c \"import PyQt6; print('PyQt6 installed')\"${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}Important Notes:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}• PyQt6 is ${RED}NOT${YELLOW} in default Debian/Ubuntu repositories${NC}"
echo -e "  You need to install it via pip: ${CYAN}pip3 install PyQt6 PyQt6-WebEngine${NC}"
echo ""
echo -e "${YELLOW}• Console mode works without PyQt6${NC}"
echo -e "  Use ${CYAN}lzfconsole${NC} if GUI doesn't work"
echo ""
echo -e "${YELLOW}• To install PyQt6 system-wide:${NC}"
echo -e "  ${CYAN}sudo pip3 install PyQt6 PyQt6-WebEngine${NC}"
echo ""
echo -e "${YELLOW}• For Kali Linux users:${NC}"
echo -e "  PyQt6 may already be available in Kali repositories"
echo ""
