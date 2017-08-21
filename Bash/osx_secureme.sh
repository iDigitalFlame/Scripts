#!/bin/bash

# MacOS Hardening/Silencing Script
# Removes all Apple callbacks and stuff
# WARNING: Will break all iCloud/Connected Apps
# Leaves your Mac a functioning BSD notebook with Aqua UI

secure_ssh()
{
  sudo rm /etc/ssh/sshd_config 2> /dev/null
  printf "Host *\n\tUseKeyChain no\n\tPasswordAuthentication yes\n\tChallengeResponseAuthentication yes\n\t" > /tmp/ssh_config
  printf "PubkeyAuthentication yes\n\tHostKeyAlgorithms ssh-ed25519-cert-v01@openssh.com,ssh-rsa-cert-v01@openssh.com,ssh-ed25519,ssh-rsa\n\t" >> /tmp/ssh_config
  printf "KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group-exchange-sha256\n\t" >> /tmp/ssh_config
  printf "Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr\n\t" >> /tmp/ssh_config
  printf "MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,hmac-ripemd160-etm@openssh.com,umac-128-etm@openssh.com,hmac-sha2-512,hmac-sha2-256,hmac-ripemd160,umac-128@openssh.com\n\t" >> /tmp/ssh_config
  printf "UseRoaming no\n\tForwardAgent no\n\tForwardX11 no\n\tGSSAPIAuthentication no\n\tGSSAPIDelegateCredentials no\n\t" >> /tmp/ssh_config
  printf "HostbasedAuthentication no\n\tStrictHostKeyChecking ask\n\tCheckHostIP yes\n\tBatchMode no\n\tAddressFamily any\n\tPort 22\n\t" >> /tmp/ssh_config
  printf "Protocol 2\n\tTunnel no\n\tConnectTimeout 30\n\tPermitLocalCommand no\n\tHashKnownHosts yes\n\tIdentityFile ~/.ssh/id_ed25519\n\t" >> /tmp/ssh_config
  printf "IdentityFile ~/.ssh/id_rsa\n\tVisualHostKey yes\n" >> /tmp/ssh_config
  sudo mv /tmp/ssh_config /etc/ssh/ssh_config
  sudo chmod 444 /etc/ssh/ssh_config
}
secure_power()
{
  sudo pmset -a destroyfvkeyonstandby 1
  sudo pmset -a hibernatemode 25
  sudo pmset -a lidwake 0
  sudo pmset -a sleep 2
  sudo pmset -a displaysleep 2
  sudo pmset -a disksleep 2
  sudo pmset -a standby 0
  sudo pmset -a standbydelay 0
  sudo pmset -a halfdim 1
  sudo pmset -a powernap 0
  sudo pmset -a autopoweroff 0
  sudo pmset -a autopoweroffdelay 0
  sudo pmset -a ttyskeepawake 0
  sudo pmset -a acwake 0
  sudo nvram AutoBoot=%03
  sudo nvram BootAudio=%00
}
secure_sysctl()
{
  echo "kern.coredump = 0" > /tmp/sysctl.conf
  echo "net.inet.icmp.icmplim = 250" >> /tmp/sysctl.conf
  echo "net.inet.icmp.drop_redirect = 1" >> /tmp/sysctl.conf
  echo "net.inet.icmp.log_redirect = 1" >> /tmp/sysctl.conf
  echo "net.inet.ip.redirect = 0" >> /tmp/sysctl.conf
  echo "net.inet.ip.sourceroute = 0" >> /tmp/sysctl.conf
  echo "net.inet.ip.accept_sourceroute = 0" >> /tmp/sysctl.conf
  echo "net.inet.icmp.bmcastecho = 0" >> /tmp/sysctl.conf
  echo "net.inet.icmp.maskrepl = 0" >> /tmp/sysctl.conf
  echo "net.inet.tcp.delayed_ack = 0" >> /tmp/sysctl.conf
  echo "net.inet.ip.forwarding = 0" >> /tmp/sysctl.conf
  echo "net.inet6.ip6.maxifprefixes = 1" >> /tmp/sysctl.conf
  echo "net.inet6.ip6.dad_count = 0" >> /tmp/sysctl.conf
  echo "net.inet6.icmp6.nodeinfo = 0" >> /tmp/sysctl.conf
  echo "net.inet6.ip6.maxfrags = 0" >> /tmp/sysctl.conf
  echo "net.inet6.ip6.maxfragpackets = 0" >> /tmp/sysctl.conf
  echo "net.inet6.ip6.use_deprecated = 0" >> /tmp/sysctl.conf
  sudo mv /tmp/sysctl.conf /etc/sysctl.conf
}
secure_configs()
{
  sudo defaults write NSGlobalDomain AppleShowAllExtensions -bool true
  defaults write NSGlobalDomain AppleShowAllExtensions -bool true
  sudo defaults write NSGlobalDomain NSDocumentSaveNewDocumentsToCloud -bool false
  defaults write NSGlobalDomain NSDocumentSaveNewDocumentsToCloud -bool false
  sudo defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true
  defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true
  sudo defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
  defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
  sudo defaults write /System/Library/LaunchDaemons/com.apple.mDNSResponder ProgramArguments -array /usr/sbin/mDNSResponder -NoMulticastAdvertisements
  sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.captive.control Active -boolean false
  sudo rm -rf "/System/Library/CoreServices/Captive Network Assistant.app"
  sudo defaults write com.apple.screensaver askForPassword -int 1
  defaults write com.apple.screensaver askForPassword -int 1
  sudo defaults write com.apple.screensaver askForPasswordDelay -int 0
  defaults write com.apple.screensaver askForPasswordDelay -int 0
  sudo defaults write /Library/Preferences/com.apple.mDNSResponder.plist NoMulticastAdvertisements -bool YES
  sudo defaults write com.apple.CrashReporter DialogType none
  defaults write com.apple.CrashReporter DialogType none
  sudo defaults write com.apple.NetworkBrowser DisableAirDrop -bool YES
  defaults write com.apple.NetworkBrowser DisableAirDrop -bool YES
  defaults write com.apple.mail-shared DisableURLLoading -bool true
  sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.AirPlayXPCHelper.plist 2> /dev/null
  sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -stop
  sudo chmod u-s /usr/bin/su
  sudo chmod u-s /usr/bin/at
  sudo chmod u-s /usr/bin/atq
  sudo chmod u-s /usr/bin/atrm
  sudo chmod u-s /usr/bin/batch
  sudo chmod u-s /usr/bin/newgrp
  sudo chmod u-s /usr/bin/quota
  defaults write com.apple.loginwindow LoginHook -string "" 2> /dev/null
  sudo systemsetup -setremoteappleevents off
  sudo systemsetup -f -setremotelogin off
  sudo systemsetup -setwakeonnetworkaccess off
  defaults write com.apple.loginwindow LogoutHook -string "" 2> /dev/null
}
secure_firewall()
{
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on 1> /dev/null
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setloggingmode on 1> /dev/null
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on 1> /dev/null
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned off 1> /dev/null
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsignedapp off 1> /dev/null
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall on 1> /dev/null
  sudo pkill -HUP socketfilterfw
}
secure_hide_app()
{
  if [ $# -gt 1 ]; then
    secure_move_app "$1" "/var/DisabledAgents/DisabledApps/"
    #sudo mv "/Applications/$1" "/var/DisabledAgents/DisabledApps/"
  else
    sudo chflags hidden "/Applications/$1"
  fi
}
secure_move_app()
{
  if [ $# -ge 3 ]; then
    tmp_hide=1
  else
    tmp_hide=0
  fi
  if ! [ -e "$2" ]; then
    sudo mkdir -p "$2"
    sudo chown root:staff "$2"
    sudo chmod 750 "$2"
  fi
  if [ -e "/Applications/$1" ]; then
    if [ -e "$2/$1" ]; then
      sudo cp -R "/Applications/$1/Contents" "$2/$1/"
      sudo rm -rf "/Applications/$1"
    else
      sudo mv "/Applications/$1" "$2/"
    fi
    if [ $tmp_hide -eq 1 ]; then
      sudo chflags hidden "$2/$1"
    else
      sudo chflags nohidden "$2/$1"
    fi
  fi
}
secure_spotlight()
{
  TMP=$(plutil -convert xml1 -o - ~/Library/Preferences/com.apple.Spotlight.plist)
  TMP=$(tr -d '\040\011\012\015' <<< $TMP)
  TMP=$(awk -F "<key>orderedItems</key><array>|</array>" '{print $2}' <<< $TMP)
  TMP=$(sed 's|<dict><key>enabled</key><true/><key>name</key><string>MENU_SPOTLIGHT_SUGGESTIONS</string></dict>|<dict><key>enabled</key><false/><key>name</key><string>MENU_SPOTLIGHT_SUGGESTIONS</string></dict>|g' <<< $TMP)
  TMP=$(sed 's|<dict><key>enabled</key><true/><key>name</key><string>MENU_DEFINITION</string></dict>|<dict><key>enabled</key><false/><key>name</key><string>MENU_DEFINITION</string></dict>|g' <<< $TMP)
  TMP=$(sed 's|<dict><key>enabled</key><true/><key>name</key><string>MENU_CONVERSION</string></dict>|<dict><key>enabled</key><false/><key>name</key><string>MENU_CONVERSION</string></dict>|g' <<< $TMP)
  defaults delete com.apple.Spotlight.plist orderedItems
  defaults write com.apple.Spotlight.plist orderedItems "<array>$TMP</array>"
  defaults write com.apple.Safari.plist UniversalSearchEnabled -bool NO
  defaults write com.apple.Safari.plist SuppressSearchSuggestions -bool YES
  defaults write com.apple.Safari.plist WebsiteSpecificSearchEnabled -bool NO
}
secure_hide_admin()
{
  if [ $# -ne 2 ]; then
    return
  fi
  if [ -e "/Users/$1" ]; then
    sudo dscl . create "/Users/$1" IsHidden 1
    sudo mv "/Users/$1" "/var/$1"
    sudo dscl . -create "/Users/$1" NFSHomeDirectory "/var/$1"
    sudo dscl . -delete "/SharePoints/$2's Public Folder"
  fi
}
secure_delete_app()
{
  sudo rm -rf "/Applications/$1"
}
secure_disable_service()
{
  if [ -f /System/Library/LaunchDaemons/$1.plist ]; then
    sudo launchctl unload -w /System/Library/LaunchDaemons/$1.plist 2> /dev/null
    launchctl unload -w /System/Library/LaunchDaemons/$1.plist 2> /dev/null
    sudo mv "/System/Library/LaunchDaemons/$1.plist" "/var/DisabledAgents/$1.plist"
    sudo sh -c "printf \"/System/Library/LaunchDaemons/$1.plist\" > \"/var/DisabledAgents/$1.plist.loc\"" 
  fi
  if [ -f /System/Library/LaunchAgents/$1.plist ]; then
    sudo launchctl unload -w /System/Library/LaunchAgents/$1.plist 2> /dev/null
    launchctl unload -w /System/Library/LaunchAgents/$1.plist 2> /dev/null
    sudo mv "/System/Library/LaunchAgents/$1.plist" "/var/DisabledAgents/$1.plist"
    sudo sh -c "printf \"/System/Library/LaunchAgents/$1.plist\" > \"/var/DisabledAgents/$1.plist.loc\""
  fi
}

if [ $UID -eq 0 ]; then
  printf "Do not run as root!\nThe program will sudo on it's own!\n"
  exit 1
fi
tmp_status=$(csrutil status | grep disabled)
if [[ -z $tmp_status && $# -eq 0 ]]; then
  printf "SIP is enabled!\nPlease disabled it first before using this!\n"
  exit 1
fi

sudo sh -c "tmp_timeout=\`cat /etc/sudoers | grep \"timestamp_timeout\"\`; if ! [[ -z \$tmp_timeout ]]; then tmp_checked=\`cat /etc/sudoers | grep \"## NEWLINE\"\`; if ! [[ -z \$tmp_checked ]]; then sed -i -e 's/## NEWLINE/Defaults timestamp_timeout=10 ##EDIT/g' /etc/sudoers; else echo \"Defaults timestamp_timeout=10 ##EDIT\" >> /etc/sudoers; fi; fi"

sudo mkdir -p "/var/DisabledAgents/DisabledApps"

secure_power
secure_configs
secure_firewall
secure_spotlight

secure_disable_service com.apple.xartstorageremoted # new
secure_disable_service com.apple.RemoteDesktop
secure_disable_service com.apple.Safari.SafeBrowsing.Service
secure_disable_service com.apple.Siri
secure_disable_service com.apple.assistantd
secure_disable_service com.apple.diagnostics_agent
secure_disable_service com.apple.helpd
secure_disable_service com.apple.imtransferagent
secure_disable_service com.apple.protectedcloudstorage.protectedcloudkeysyncing
secure_disable_service com.apple.screensharing.MessagesAgent
secure_disable_service com.apple.screensharing.agent
secure_disable_service com.apple.screensharing
secure_disable_service com.apple.AppleFileServer
secure_disable_service com.apple.applessdstatistics
secure_disable_service com.apple.captiveagent
secure_disable_service com.apple.coreservices.appleid.passwordcheck
secure_disable_service com.apple.xsan
secure_disable_service com.apple.xsandaily
secure_disable_service com.apple.icloud.fmfd
secure_disable_service com.apple.remotepairtool
secure_disable_service com.apple.rpmuxd #headphones?
secure_disable_service com.apple.icloud.findmydeviced 
secure_disable_service com.apple.findmymacmessenger
secure_disable_service com.apple.familycontrols
secure_disable_service com.apple.findmymac
secure_disable_service com.apple.SubmitDiagInfo
secure_disable_service com.apple.appleseed.fbahelperd
secure_disable_service com.apple.apsd
secure_disable_service com.apple.AOSNotificationOSX
secure_disable_service com.apple.FileSyncAgent.sshd
secure_disable_service com.apple.ManagedClient.cloudconfigurationd
secure_disable_service com.apple.iCloudStats
secure_disable_service com.apple.locationd
secure_disable_service com.apple.mbicloudsetupd
secure_disable_service com.apple.awacsd
secure_disable_service com.apple.awdd
secure_disable_service com.apple.CrashReporterSupportHelper
secure_disable_service com.apple.photoanalysisd
secure_disable_service com.apple.telephonyutilities.callservicesd
secure_disable_service com.apple.AirPortBaseStationAgent
secure_disable_service com.apple.familycircled
secure_disable_service com.apple.familycontrols.useragent
secure_disable_service com.apple.familynotificationd
secure_disable_service com.apple.gamed
secure_disable_service com.apple.imagent
secure_disable_service com.apple.cloudfamilyrestrictionsd-mac
secure_disable_service com.apple.cloudpaird
secure_disable_service com.apple.cloudphotosd
secure_disable_service com.apple.DictationIM
secure_disable_service com.apple.assistant_service
secure_disable_service com.apple.CallHistorySyncHelper
secure_disable_service com.apple.CallHistoryPluginHelper
secure_disable_service com.apple.AOSPushRelay
secure_disable_service com.apple.IMLoggingAgent
secure_disable_service com.apple.geodMachServiceBridge
secure_disable_service com.apple.syncdefaultsd
secure_disable_service com.apple.security.cloudkeychainproxy3
secure_disable_service com.apple.security.idskeychainsyncingproxy
secure_disable_service com.apple.security.keychain-circle-notification
secure_disable_service com.apple.sharingd
secure_disable_service com.apple.appleseed.seedusaged
secure_disable_service com.apple.cloudd
secure_disable_service com.apple.parentalcontrols.check
secure_disable_service com.apple.parsecd
secure_disable_service com.apple.identityservicesd
secure_disable_service com.apple.bird
secure_disable_service com.apple.passd
secure_disable_service com.apple.CommCenter-osx
secure_disable_service com.apple.Maps.pushdaemon
secure_disable_service com.apple.security.keychainsyncingoveridsproxy
secure_disable_service com.apple.rtcreportingd
secure_disable_service com.apple.SafariCloudHistoryPushAgent
secure_disable_service com.apple.safaridavclient
secure_disable_service com.apple.SafariNotificationAgent
secure_disable_service com.apple.iCloudUserNotifications
secure_disable_service com.apple.icloud.fmfd.plist
secure_disable_service com.apple.AddressBook.AssistantService
secure_disable_service com.apple.AddressBook.ContactsAccountsService
secure_disable_service com.apple.AddressBook.SourceSync
secure_disable_service com.apple.AddressBook.abd
secure_disable_service com.apple.ContactsAgent
secure_disable_service com.apple.java.InstallOnDemand
secure_disable_service com.apple.java.updateSharing
secure_disable_service com.apple.videosubscriptionsd      
secure_disable_service com.apple.icloud.findmydeviced.findmydevice-user-agent      
secure_disable_service com.apple.GameController.gamecontrollerd
secure_disable_service com.apple.coreservices.appleid.authentication

secure_move_app "Safari.app" "/Applications/Utilities" 1
secure_delete_app "Messages.app"
secure_delete_app "FaceTime.app"
secure_delete_app "Contacts.app"
secure_delete_app "Maps.app"
secure_delete_app "Chess.app"
secure_delete_app "iBooks.app"
secure_delete_app "DVD Player.app"
secure_delete_app "Photo Booth.app"
secure_delete_app "Utilities/Migration Assistant.app"
secure_move_app "Automator.app" "/Applications/Utilities" 1
secure_move_app "Image Capture.app" "/Applications/Utilities"
secure_move_app "Dictionary.app" "/Applications/Utilities" 1
secure_move_app "Font Book.app" "/Applications/Utilities" 1
secure_move_app "Mission Control.app" "/Applications/Utilities"
secure_move_app "Preview.app" "/Applications/Utilities" 1
secure_move_app "QuickTime Player.app" "/Applications/Utilities" 1
secure_move_app "Dashboard.app" "/Applications/Utilities" 1
secure_move_app "Stickies.app" "/Applications/Utilities" 1
secure_move_app "Siri.app" "/Applications/Utilities" 1
secure_delete_app "Utilities/Siri.app"
secure_move_app "TextEdit.app" "/Applications/Utilities"
secure_move_app "Time Machine.app" "/Applications/Utilities"
secure_hide_app "Utilities/Boot Camp Assistant.app"
secure_delete_app "Utilities/Boot Camp Assistant.app"
secure_hide_app "Utilities/ColorSync Utility.app"
secure_hide_app "Utilities/AirPort Utility.app"
secure_hide_app "Utilities/Audio MIDI Setup.app"
secure_delete_app "Utilities/Audio MIDI Setup.app"
secure_hide_app "Utilities/Digital Color Meter.app"
secure_hide_app "Utilities/Grapher.app"
secure_hide_app "Utilities/VoiceOver Utility.app"
secure_delete_app "Utilities/VoiceOver Utility.app"

secure_ssh
secure_sysctl
# Fill out these options then uncommend
# secure_hide_admin "<admin_uname>" "<Admin Name>"

duti -s com.apple.Safari afp
duti -s com.apple.Safari ftp
duti -s com.apple.Safari nfs
duti -s com.apple.Safari smb

tmp_timeout=$(sudo cat /etc/sudoers | grep "Defaults timestamp_timeout=10 ##EDIT")
if ! [[ -z $tmp_timeout ]]; then
  sudo sed -i -e 's/Defaults timestamp_timeout=10 ##EDIT/## NEWLINE/g' /etc/sudoers
fi
echo "Done!"

