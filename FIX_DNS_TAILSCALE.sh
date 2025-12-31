#!/bin/bash
# FIX_DNS_TAILSCALE.sh
#
# Fixes Tailscale DNS blocking data.nationalgrideso.com
#
# ISSUE: Tailscale DNS (100.100.100.100) uses split DNS which blocks
# certain external domains like data.nationalgrideso.com
#
# SOLUTION 1: Add fallback DNS servers (temporary - survives until reboot)
# SOLUTION 2: Disable Tailscale DNS (permanent)

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          TAILSCALE DNS FIX FOR NESO DATA ACCESS                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "Current DNS configuration:"
echo "─────────────────────────────────────────"
cat /etc/resolv.conf
echo "─────────────────────────────────────────"
echo ""

echo "Testing DNS resolution:"
echo "  • google.com:               $(nslookup google.com 8.8.8.8 2>&1 | grep -q 'Address:' && echo '✅ WORKS' || echo '❌ FAILS')"
echo "  • data.nationalgrideso.com: $(nslookup data.nationalgrideso.com 2>&1 | grep -q 'answer' || echo '❌ BLOCKED BY TAILSCALE')"
echo ""

echo "Choose a fix:"
echo ""
echo "OPTION 1: Add fallback DNS (temporary, survives until reboot)"
echo "──────────────────────────────────────────────────────────────"
echo "  sudo bash -c 'cat >> /etc/resolv.conf << EOF"
echo "# Fallback DNS for blocked domains"
echo "nameserver 8.8.8.8"
echo "nameserver 1.1.1.1"
echo "EOF'"
echo ""

echo "OPTION 2: Disable Tailscale DNS (permanent, recommended)"
echo "──────────────────────────────────────────────────────────────"
echo "  tailscale up --accept-dns=false"
echo "  sudo systemctl restart systemd-resolved"
echo ""

echo "OPTION 3: Use Tailscale exit node with better DNS"
echo "──────────────────────────────────────────────────────────────"
echo "  tailscale exit-node list"
echo "  tailscale up --exit-node=<node-name>"
echo ""

read -p "Apply OPTION 1 now? (y/N): " choice
if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    echo ""
    echo "📝 Adding fallback DNS servers..."

    # Backup current resolv.conf
    sudo cp /etc/resolv.conf /etc/resolv.conf.backup.$(date +%Y%m%d_%H%M%S)

    # Add fallback DNS
    sudo bash -c 'cat >> /etc/resolv.conf << EOF
# Fallback DNS for blocked domains (added $(date))
nameserver 8.8.8.8
nameserver 1.1.1.1
EOF'

    echo "✅ DNS servers added!"
    echo ""
    echo "Testing fix:"
    nslookup data.nationalgrideso.com 8.8.8.8

    echo ""
    echo "⚠️  NOTE: Tailscale may overwrite /etc/resolv.conf on restart"
    echo "    For permanent fix, use: tailscale up --accept-dns=false"
else
    echo "No changes made. Run commands manually as needed."
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  NOTE: Current scripts use BigQuery data (no external API)       ║"
echo "║  This fix is OPTIONAL - only needed if you add NESO API calls    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
